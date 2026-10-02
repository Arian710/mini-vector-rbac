"""
Web-API fuer MiniVectorDB (FastAPI) mit echtem JWT-Login.

Ablauf:
1. Client ruft POST /login mit username+password auf, bekommt bei Erfolg ein
   signiertes JWT zurueck.
2. Client ruft POST /search auf und schickt das JWT im Authorization-Header
   ("Authorization: Bearer <token>").
3. Die API prueft die Signatur (auth.decode_access_token) und entnimmt
   Username UND Rolle direkt aus dem TOKEN - nicht mehr aus dem Request-Body.
   Ein Client kann sich also weder eine andere Rolle noch einen anderen
   Username zuschreiben, ohne den Server-seitigen JWT_SECRET_KEY zu kennen.
4. Jede Suche wird protokolliert (storage.log_search). /audit-log zeigt dieses
   Protokoll - aber nur der Rolle management (Authentication reicht hier nicht,
   es braucht zusaetzlich Authorization: siehe require_management()).

Start:
    python seed_data.py     # einmalig, befuellt die Datenbank
    uvicorn api:app --reload
Swagger-UI: http://127.0.0.1:8000/docs
"""

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

import os
from typing import List, Optional

import jwt
import requests
from fastapi import Depends, FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

import auth
import documents
import role_suggestion
import storage
from db import MiniVectorDB
from demo import DEMO_HTML
from embeddings import get_default_embedder

app = FastAPI(
    title="Mini Vector DB mit RBAC",
    description="Brute-Force-Vektorsuche mit serverseitig erzwungenem Rollenfilter und echtem JWT-Login.",
    version="2.0.0",
)

# Rate-Limiting pro IP - verhindert automatisiertes Passwort-Durchprobieren
# gegen /login. Zaehlt NUR die IP, nicht den Username, damit ein Angreifer
# nicht durch Rotieren der Zielnamen um das Limit herumkommt.
# DISABLE_RATE_LIMIT=1 fuer Tests, die bewusst oft hintereinander einloggen
# (test_tenancy.py/test_audit.py) - setzt die Variable VOR dem Import von api,
# genau wie beim Azure-Embedder-Test-Fallback (siehe dort fuer die Begruendung).
limiter = Limiter(key_func=get_remote_address, enabled=os.environ.get("DISABLE_RATE_LIMIT") != "1")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Erlaubt dem React-Dashboard (laeuft im Dev-Modus auf einem anderen Port),
# die API vom Browser aus anzusprechen. Nur fuer lokale Entwicklung offen.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

storage.init_db()
# WICHTIG: derselbe Embedder, der auch beim Seeden benutzt wurde (seed_data.py) -
# sonst landet die Query in einem anderen Vektorraum als die gespeicherten Tickets.
db = MiniVectorDB(embedder=get_default_embedder())
for _ticket in storage.load_tickets():
    db.load_entry(_ticket["id"], _ticket["text"], _ticket["vector"],
                   _ticket["allowed_roles"], _ticket["tenant_id"], _ticket["customer_label"],
                   _ticket["source_document"], _ticket["chunk_index"], _ticket["chunk_total"])

_security = HTTPBearer()


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class SearchRequest(BaseModel):
    query: str
    top_k: int = 3


class SearchResult(BaseModel):
    id: int
    text: str
    score: float
    source_document: Optional[str] = None
    chunk_index: Optional[int] = None
    chunk_total: Optional[int] = None


class AuditLogEntry(BaseModel):
    username: str
    query: str
    result_count: int
    created_at: str


class GraphNode(BaseModel):
    id: int
    text: str
    restricted: bool
    customer_label: Optional[str] = None
    source_document: Optional[str] = None


class GraphEdge(BaseModel):
    source: int
    target: int
    weight: float


class GraphResponse(BaseModel):
    nodes: List[GraphNode]
    edges: List[GraphEdge]


class SuggestResponse(BaseModel):
    text: str
    suggested_role: str
    reasons: List[str]
    chunk_count: int  # wie viele Abschnitte beim Speichern entstehen (1 = kein Chunking noetig)
    ocr_used: bool = False  # True, wenn die PDF keine Text-Ebene hatte und Azure OCR eingesprungen ist


class SaveDocumentRequest(BaseModel):
    text: str
    allowed_role: str  # "all" oder "management" - vom Menschen bestaetigt/gewaehlt
    customer_label: Optional[str] = None
    source_document_name: Optional[str] = None  # z.B. der urspruengliche Dateiname


class SaveDocumentResponse(BaseModel):
    ids: List[int]
    chunk_count: int
    allowed_role: str


class RoleOut(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    is_system: bool


class CreateRoleRequest(BaseModel):
    name: str
    description: Optional[str] = None


class UpdateRoleRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(_security)) -> dict:
    """Authentication: prueft das Token und liefert {username, role, tenant_id} daraus -
    niemals aus dem Request-Body."""
    try:
        return auth.decode_access_token(credentials.credentials)
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Ungültiges oder abgelaufenes Token")


def require_management(current_user: dict = Depends(get_current_user)) -> dict:
    """Authorization: baut auf get_current_user auf (muss zuerst gueltig eingeloggt sein),
    prueft zusaetzlich, ob die Rolle das Recht fuer DIESEN Endpunkt hat."""
    if current_user["role"] != "management":
        raise HTTPException(status_code=403, detail="Nur für die Rolle management sichtbar")
    return current_user


def _safe_embed(text: str):
    """Wrappt db.embed() mit einer verstaendlichen Fehlermeldung statt einer
    rohen 500er-Antwort - ohne das wuerde ein Azure-Ausfall (Rate-Limit,
    Timeout, Netzwerk) im Browser nur als nicht-greifbares "Failed to fetch"
    ankommen, weil eine unbehandelte Exception die CORS-Header der Antwort
    verliert und der Browser den eigentlichen Fehler nicht mehr zeigt."""
    try:
        return db.embed(text)
    except requests.exceptions.RequestException as e:
        raise HTTPException(
            status_code=502,
            detail=f"Embedding-Dienst momentan nicht erreichbar, bitte kurz erneut versuchen ({e}).",
        )


@app.get("/health")
def health():
    return {"status": "ok", "tickets_indexed": len(db)}


@app.get("/demo", response_class=HTMLResponse)
def demo_page():
    """Visuelle Live-Demo fuer Vorfuehrungen/Demo-GIFs - kein Terminal noetig."""
    return DEMO_HTML


@app.post("/login", response_model=TokenResponse)
@limiter.limit("5/minute")
def login(request: Request, body: LoginRequest):
    # slowapi erwartet den Parameternamen woertlich "request" fuer das
    # Starlette-Request-Objekt (liest daraus die Client-IP) - der JSON-Body
    # heisst deshalb hier "body", nicht wie sonst ueblich "request".
    try:
        identity = auth.authenticate(body.username, body.password)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
    token = auth.create_access_token(body.username, identity["role"], identity["tenant_id"])
    return TokenResponse(access_token=token)


@app.post("/search", response_model=List[SearchResult])
def search(request: SearchRequest, current_user: dict = Depends(get_current_user)):
    try:
        results = db.search(
            request.query,
            role=current_user["role"],
            tenant_id=current_user["tenant_id"],
            top_k=request.top_k,
        )
    except requests.exceptions.RequestException as e:
        raise HTTPException(
            status_code=502,
            detail=f"Embedding-Dienst momentan nicht erreichbar, bitte kurz erneut versuchen ({e}).",
        )
    storage.log_search(current_user["username"], current_user["tenant_id"], request.query, len(results))
    return results


@app.get("/graph-data", response_model=GraphResponse)
def graph_data(current_user: dict = Depends(get_current_user)):
    """Knoten+Kanten fuer die Graph-Ansicht - derselbe Tenant-/RBAC-Filter wie /search."""
    return db.graph_data(role=current_user["role"], tenant_id=current_user["tenant_id"])


@app.post("/documents/suggest", response_model=SuggestResponse)
def suggest_document(
    file: UploadFile = File(...),
    current_user: dict = Depends(require_management),
):
    """
    Schritt 1 des Selfservice-Uploads: extrahiert Text aus PDF/DOCX/TXT und
    liefert einen Rollenvorschlag - speichert NICHTS. Erst /documents (Schritt 2)
    schreibt tatsaechlich, nachdem ein Mensch die Rolle bestaetigt/geaendert hat.
    """
    try:
        raw = file.file.read()
        text, ocr_used = documents.extract_text(file.filename, raw)
    except documents.UnsupportedFileType as e:
        raise HTTPException(status_code=422, detail=str(e))

    chunks = documents.chunk_text(text)
    # Fuer den Rollenvorschlag reicht ein repraesentativer Vektor (der erste
    # Abschnitt) - die Keyword-Heuristik in role_suggestion.py scannt trotzdem
    # den VOLLEN Text, nur die Embedding-Aehnlichkeit basiert auf Abschnitt 1.
    # Beim tatsaechlichen Speichern (save_document) wird JEDER Abschnitt einzeln
    # eingebettet, hier geht es nur um eine schnelle Vorschau.
    vector = _safe_embed(chunks[0])
    tenant_entries = db.entries_for_tenant(current_user["tenant_id"])
    tenant_roles = storage.list_roles(current_user["tenant_id"])
    suggestion = role_suggestion.suggest_role(text, vector, tenant_entries, tenant_roles)

    return SuggestResponse(text=text, chunk_count=len(chunks), ocr_used=ocr_used, **suggestion)


@app.post("/documents", response_model=SaveDocumentResponse)
def save_document(
    request: SaveDocumentRequest,
    current_user: dict = Depends(require_management),
):
    """Schritt 2: speichert das Dokument mit der vom Menschen bestaetigten Rolle -
    persistent (storage.py) UND sofort im laufenden Suchindex (db.add()), ohne
    Server-Neustart. tenant_id kommt aus dem JWT, niemals vom Client."""
    tenant_id = current_user["tenant_id"]
    valid_role_names = {r["name"] for r in storage.list_roles(tenant_id)}
    if request.allowed_role not in valid_role_names:
        raise HTTPException(
            status_code=422,
            detail=f"allowed_role '{request.allowed_role}' ist keine Rolle dieses Tenants "
                    f"(gueltig: {', '.join(sorted(valid_role_names))}).",
        )

    allowed_roles = [request.allowed_role]

    chunks = documents.chunk_text(request.text)
    chunk_total = len(chunks) if len(chunks) > 1 else None  # None = kein Chunking noetig/erfolgt
    ids = []

    for i, chunk in enumerate(chunks, start=1):
        new_id = storage.next_ticket_id()
        vector = _safe_embed(chunk)
        chunk_index = i if chunk_total else None

        storage.save_ticket(new_id, chunk, vector, allowed_roles, tenant_id, request.customer_label,
                             request.source_document_name, chunk_index, chunk_total)
        # load_entry statt add(): der Vektor wurde oben schon berechnet - load_entry
        # nutzt ihn direkt, statt beim Azure-Embedder ein zweites Mal (und ein
        # zweites Mal kostenpflichtig) nachzufragen.
        db.load_entry(new_id, chunk, vector, allowed_roles, tenant_id, request.customer_label,
                       request.source_document_name, chunk_index, chunk_total)
        ids.append(new_id)

    return SaveDocumentResponse(ids=ids, chunk_count=len(chunks), allowed_role=request.allowed_role)


def _role_anchor_vector(name: str, description: str):
    """Embedding-Anker einer Rolle aus Name+Beschreibung - loest das Kaltstart-
    Problem im Rollenvorschlag (siehe role_suggestion.py): eine neue Rolle hat
    sofort einen Vergleichswert, auch ohne ein einziges zugewiesenes Dokument."""
    if not description:
        return None
    return _safe_embed(f"{name}: {description}")


@app.get("/roles", response_model=List[RoleOut])
def list_roles(current_user: dict = Depends(require_management)):
    return storage.list_roles(current_user["tenant_id"])


@app.post("/roles", response_model=RoleOut)
def create_role(request: CreateRoleRequest, current_user: dict = Depends(require_management)):
    tenant_id = current_user["tenant_id"]
    vector = _role_anchor_vector(request.name, request.description)
    try:
        role_id = storage.create_role(tenant_id, request.name, request.description, vector)
    except storage.DuplicateRoleName as e:
        raise HTTPException(status_code=409, detail=str(e))
    return RoleOut(id=role_id, name=request.name, description=request.description, is_system=False)


@app.patch("/roles/{role_id}", response_model=RoleOut)
def update_role(role_id: int, request: UpdateRoleRequest, current_user: dict = Depends(require_management)):
    tenant_id = current_user["tenant_id"]
    vector = None
    if request.description is not None:
        name_for_anchor = request.name or next(
            (r["name"] for r in storage.list_roles(tenant_id) if r["id"] == role_id), None
        )
        vector = _role_anchor_vector(name_for_anchor, request.description)

    try:
        storage.update_role(role_id, tenant_id, name=request.name, description=request.description, vector=vector)
    except storage.DuplicateRoleName as e:
        raise HTTPException(status_code=409, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))

    updated = next((r for r in storage.list_roles(tenant_id) if r["id"] == role_id), None)
    return RoleOut(id=updated["id"], name=updated["name"], description=updated["description"],
                    is_system=updated["is_system"])


@app.delete("/roles/{role_id}")
def delete_role(role_id: int, current_user: dict = Depends(require_management)):
    tenant_id = current_user["tenant_id"]
    try:
        storage.delete_role(role_id, tenant_id)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except storage.RoleInUse as e:
        raise HTTPException(status_code=409, detail=str(e))
    return {"deleted": role_id}


@app.get("/audit-log", response_model=List[AuditLogEntry])
def audit_log(current_user: dict = Depends(require_management)):
    # Nur das Protokoll des EIGENEN Tenants - sonst wuerde management eines
    # Mandanten sehen, wonach ein anderer Mandant gesucht hat.
    return storage.load_search_log(tenant_id=current_user["tenant_id"])

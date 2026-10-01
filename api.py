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

from typing import List

import jwt
from fastapi import Depends, FastAPI, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel

import auth
import storage
from db import MiniVectorDB
from embeddings import get_default_embedder

app = FastAPI(
    title="Mini Vector DB mit RBAC",
    description="Brute-Force-Vektorsuche mit serverseitig erzwungenem Rollenfilter und echtem JWT-Login.",
    version="2.0.0",
)

storage.init_db()
# WICHTIG: derselbe Embedder, der auch beim Seeden benutzt wurde (seed_data.py) -
# sonst landet die Query in einem anderen Vektorraum als die gespeicherten Tickets.
db = MiniVectorDB(embedder=get_default_embedder())
for _ticket in storage.load_tickets():
    db.load_entry(_ticket["id"], _ticket["text"], _ticket["vector"], _ticket["allowed_roles"])

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


class AuditLogEntry(BaseModel):
    username: str
    query: str
    result_count: int
    created_at: str


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(_security)) -> dict:
    """Authentication: prueft das Token und liefert {username, role} daraus - niemals aus dem Request-Body."""
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


@app.get("/health")
def health():
    return {"status": "ok", "tickets_indexed": len(db)}


@app.post("/login", response_model=TokenResponse)
def login(request: LoginRequest):
    try:
        role = auth.authenticate(request.username, request.password)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
    token = auth.create_access_token(request.username, role)
    return TokenResponse(access_token=token)


@app.post("/search", response_model=List[SearchResult])
def search(request: SearchRequest, current_user: dict = Depends(get_current_user)):
    results = db.search(request.query, role=current_user["role"], top_k=request.top_k)
    storage.log_search(current_user["username"], request.query, len(results))
    return results


@app.get("/audit-log", response_model=List[AuditLogEntry])
def audit_log(current_user: dict = Depends(require_management)):
    return storage.load_search_log()

"""
Web-API fuer MiniVectorDB (FastAPI).

WICHTIGER DESIGN-PUNKT (Konzept 5, jetzt als echte HTTP-API): der Client
schickt einen `username`, NIEMALS eine Rolle direkt. Die Rolle wird
ausschliesslich serverseitig ueber auth.get_role() nachgeschlagen. Wuerde
stattdessen z.B. `role` als Feld im Request-Body akzeptiert, koennte sich
jeder Client einfach selbst zu "management" erklaeren - der ganze Rollenfilter
in db.py waere wertlos. Das ist derselbe Grundsatz aus unserem Dialog, nur
jetzt an der echten Netzwerkgrenze durchgesetzt statt nur als Funktionsaufruf.

Start:
    uvicorn api:app --reload
Dann Swagger-UI unter http://127.0.0.1:8000/docs
"""

from typing import List

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from auth import USERS, get_role
from data import TICKETS
from db import MiniVectorDB
from embeddings import get_default_embedder

app = FastAPI(
    title="Mini Vector DB mit RBAC",
    description="Brute-Force-Vektorsuche mit serverseitig erzwungenem Rollenfilter.",
    version="1.0.0",
)

_embedder = get_default_embedder()
db = MiniVectorDB(embedder=_embedder)
for _ticket in TICKETS:
    db.add(_ticket["id"], _ticket["text"], _ticket["allowed_roles"])


class SearchRequest(BaseModel):
    username: str
    query: str
    top_k: int = 3


class SearchResult(BaseModel):
    id: int
    text: str
    score: float


@app.get("/health")
def health():
    return {
        "status": "ok",
        "embedder": type(_embedder).__name__,
        "tickets_indexed": len(TICKETS),
    }


@app.post("/search", response_model=List[SearchResult])
def search(request: SearchRequest):
    """
    Sucht Tickets fuer den angegebenen User.

    Die Rolle wird NIE aus dem Request uebernommen, sondern serverseitig ueber
    auth.get_role(username) bestimmt - siehe Moduldocstring oben.
    """
    if request.username not in USERS:
        raise HTTPException(status_code=401, detail="Unbekannter User")

    role = get_role(request.username)
    return db.search(request.query, role=role, top_k=request.top_k)

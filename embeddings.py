"""
Embedder-Abstraktion (Konzept 2).

MiniVectorDB kennt nur das Embedder-Interface, nie die konkrete Implementierung.
Dadurch laesst sich das Embedding-Backend austauschen, ohne db.py anzufassen -
und Tests koennen bewusst den kostenlosen, deterministischen HashingEmbedder
erzwingen, statt bei jedem Testlauf echtes Geld fuer Azure-API-Aufrufe
auszugeben oder eine Internetverbindung zu brauchen.

- HashingEmbedder:     Platzhalter-Embedding (Wortueberlappung), offline, gratis.
- AzureOpenAIEmbedder: echtes, trainiertes Embedding-Modell via Azure OpenAI.
"""

import hashlib
import os
import re
from abc import ABC, abstractmethod

import numpy as np
import requests


class Embedder(ABC):
    """Gemeinsames Interface: jeder Embedder uebersetzt Text in einen Vektor."""

    @abstractmethod
    def embed(self, text: str) -> np.ndarray:
        raise NotImplementedError


class HashingEmbedder(Embedder):
    """
    Vereinfachtes Platzhalter-Embedding (Hashing-Trick / Bag-of-Words).

    Kein trainiertes Modell - zaehlt nur Wortueberlappung nach Stoppwort-Filter.
    Erkennt keine Synonyme, ist aber deterministisch, kostenlos und offline
    lauffaehig. Wird deshalb fest in den Tests verwendet (siehe test_rbac.py).
    """

    STOPWORDS = {
        "der", "die", "das", "und", "ist", "im", "in", "zu", "auf", "fuer",
        "mit", "von", "wird", "wurde", "ein", "eine", "einen", "einem",
        "nicht", "mehr", "noch", "sich", "bei", "um", "als", "an", "aus",
        "dem", "des", "den", "sind", "hat", "haben", "werden", "ueber",
        "seit", "heute",
    }
    _WORD_RE = re.compile(r"[a-zäöüß]+")

    def __init__(self, dim: int = 64):
        self.dim = dim

    def _tokenize(self, text: str) -> list:
        words = self._WORD_RE.findall(text.lower())
        return [w for w in words if w not in self.STOPWORDS and len(w) > 2]

    def _hash_index(self, word: str) -> int:
        # md5 statt Pythons eingebautem hash(): der ist pro Prozess randomisiert,
        # wir brauchen aber reproduzierbare Vektoren ueber mehrere Laeufe hinweg.
        digest = hashlib.md5(word.encode("utf-8")).hexdigest()
        return int(digest, 16) % self.dim

    def embed(self, text: str) -> np.ndarray:
        vector = np.zeros(self.dim)
        for word in self._tokenize(text):
            vector[self._hash_index(word)] += 1.0
        return vector


class AzureOpenAIEmbedder(Embedder):
    """
    Echtes, trainiertes Embedding-Modell ueber die Azure OpenAI REST-API.

    Erwartet drei Umgebungsvariablen (siehe .env.example):
      AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_API_KEY, AZURE_OPENAI_EMBEDDING_DEPLOYMENT
    """

    API_VERSION = "2023-05-15"

    def __init__(self, endpoint: str = None, api_key: str = None, deployment: str = None):
        self.endpoint = (endpoint or os.environ["AZURE_OPENAI_ENDPOINT"]).rstrip("/")
        self.api_key = api_key or os.environ["AZURE_OPENAI_API_KEY"]
        self.deployment = deployment or os.environ["AZURE_OPENAI_EMBEDDING_DEPLOYMENT"]

    def embed(self, text: str) -> np.ndarray:
        url = (
            f"{self.endpoint}/openai/deployments/{self.deployment}"
            f"/embeddings?api-version={self.API_VERSION}"
        )
        response = requests.post(
            url,
            headers={"api-key": self.api_key, "Content-Type": "application/json"},
            json={"input": text},
            timeout=30,
        )
        response.raise_for_status()
        embedding = response.json()["data"][0]["embedding"]
        return np.array(embedding)


def get_default_embedder() -> Embedder:
    """
    Waehlt automatisch Azure, wenn vollstaendige Zugangsdaten in der Umgebung
    vorhanden sind - sonst faellt es zurueck auf den kostenlosen Hashing-
    Embedder. So bleibt das Projekt auch fuer jeden lauffaehig, der es klont,
    ohne eine eigene Azure-Ressource eingerichtet zu haben.
    """
    required_vars = [
        "AZURE_OPENAI_ENDPOINT",
        "AZURE_OPENAI_API_KEY",
        "AZURE_OPENAI_EMBEDDING_DEPLOYMENT",
    ]
    if all(os.environ.get(var) for var in required_vars):
        return AzureOpenAIEmbedder()
    return HashingEmbedder()

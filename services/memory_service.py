"""
Semantic memory service.

PHASE 5: lets Continuity retrieve health events that are semantically
related to each other - e.g. "my knee is acting up" and "my leg is sore
again" should surface as related, even though they share almost no words.

WHERE QDRANT IS USED:
- If QDRANT_URL is set (see .env), index_event() and find_related_events()
  store/search vectors in a Qdrant collection called "health_events".
- If QDRANT_URL is missing, or the Qdrant server can't be reached, both
  functions transparently fall back to a local SQLite table
  (event_embedding, in database/db.py) and compute cosine similarity with
  numpy instead. The app works exactly the same either way - Qdrant just
  makes it a real vector database instead of a local approximation.

Embeddings are generated locally with sentence-transformers (no API key
needed), so this feature keeps working even if the LLM API key isn't set.
The first run downloads a small model (~80MB) - that requires internet
access once, then it's cached.
"""

import os
from typing import List, Optional

import numpy as np

from database import db

QDRANT_COLLECTION = "health_events"
EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"
DEFAULT_MIN_SCORE = 0.45   # cosine similarity threshold - tuned to avoid
                           # merging unrelated symptoms (see spec: don't
                           # falsely merge "knee pain" with "headache")

_embedder = None


def _get_embedder():
    """Loads the sentence-transformers model once and reuses it."""
    global _embedder
    if _embedder is None:
        from sentence_transformers import SentenceTransformer
        _embedder = SentenceTransformer(EMBEDDING_MODEL_NAME)
    return _embedder


def embed_text(text: str) -> List[float]:
    model = _get_embedder()
    vector = model.encode(text, normalize_embeddings=True)
    return vector.tolist()


def _get_qdrant_client():
    """Returns a connected Qdrant client, or None if not configured/reachable."""
    url = os.environ.get("QDRANT_URL")
    if not url:
        return None

    try:
        from qdrant_client import QdrantClient
    except ImportError:
        return None

    try:
        api_key = os.environ.get("QDRANT_API_KEY") or None
        client = QdrantClient(url=url, api_key=api_key)
        client.get_collections()  # cheap call to confirm it's reachable
        return client
    except Exception:
        return None


def _ensure_collection(client, dim: int) -> None:
    from qdrant_client.models import Distance, VectorParams

    existing = [c.name for c in client.get_collections().collections]
    if QDRANT_COLLECTION not in existing:
        client.create_collection(
            collection_name=QDRANT_COLLECTION,
            vectors_config=VectorParams(size=dim, distance=Distance.COSINE),
        )


def index_event(event_id: int, text: str) -> None:
    """
    Store this event's embedding so it can be found later.
    Tries Qdrant first (if configured), falls back to local SQLite.
    """
    vector = embed_text(text)

    client = _get_qdrant_client()
    if client is not None:
        try:
            from qdrant_client.models import PointStruct
            _ensure_collection(client, len(vector))
            client.upsert(
                collection_name=QDRANT_COLLECTION,
                points=[PointStruct(id=event_id, vector=vector,
                                     payload={"event_id": event_id})],
            )
            return
        except Exception:
            pass  # fall through to local fallback below

    db.save_event_embedding(event_id, vector)


def find_related_events(
    query_text: str,
    exclude_event_id: Optional[int] = None,
    top_k: int = 5,
    min_score: float = DEFAULT_MIN_SCORE,
) -> List[int]:
    """
    Returns a list of event IDs whose stored embedding is semantically
    close to query_text, best match first. Does NOT include exclude_event_id.
    """
    vector = np.array(embed_text(query_text))

    client = _get_qdrant_client()
    if client is not None:
        try:
            _ensure_collection(client, len(vector))
            results = client.search(
                collection_name=QDRANT_COLLECTION,
                query_vector=vector.tolist(),
                limit=top_k + 1,
            )
            ids = [
                r.id for r in results
                if r.score >= min_score and r.id != exclude_event_id
            ]
            return ids[:top_k]
        except Exception:
            pass  # fall through to local fallback below

    # Local fallback: cosine similarity over everything stored in SQLite
    scored = []
    for event_id, stored_vector in db.get_all_event_embeddings():
        if event_id == exclude_event_id:
            continue
        v = np.array(stored_vector)
        denom = (np.linalg.norm(vector) * np.linalg.norm(v)) or 1e-8
        score = float(np.dot(vector, v) / denom)
        if score >= min_score:
            scored.append((event_id, score))

    scored.sort(key=lambda pair: pair[1], reverse=True)
    return [event_id for event_id, _ in scored[:top_k]]

from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, HTTPException, Query
from rapidfuzz.distance import JaroWinkler

from app.repositories.names import NamesRepository
from app.services.normalizer import normalize

names_repo: NamesRepository | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global names_repo
    names_repo = NamesRepository()
    names_repo.load()
    yield


app = FastAPI(
    title="Name Similarity API",
    description="API to find similar names in a historical database using Jaro-Winkler algorithm",
    version="1.0.0",
    lifespan=lifespan,
)


@app.get("/search")
async def search_names(
    name: str = Query(..., min_length=1, description="Full name to search for"),
    threshold: float = Query(
        70.0, ge=0, le=100, description="Minimum similarity percentage (0-100)"
    ),
    limit: int = Query(
        100, ge=1, le=1000, description="Maximum number of results to return"
    ),
    use_blocking: bool = Query(
        True, description="Use prefix blocking to reduce search space (faster for large datasets)"
    ),
) -> dict[str, Any]:
    if names_repo is None:
        raise HTTPException(status_code=503, detail="Service not initialized")

    query_normalized = normalize(name)
    results = []

    if use_blocking:
        candidates = names_repo.candidates_for(name)
    else:
        candidates = list(names_repo)

    for record_id, db_name, db_normalized in candidates:
        similarity = JaroWinkler.similarity(query_normalized, db_normalized) * 100
        if similarity >= threshold:
            results.append((record_id, db_name, similarity))

    results.sort(key=lambda x: x[2], reverse=True)
    results = results[:limit]

    return {
        str(record_id): {"name": db_name, "similarity": round(similarity, 2)}
        for record_id, db_name, similarity in results
    }


@app.get("/health")
async def health():
    if names_repo is None:
        raise HTTPException(status_code=503, detail="Service not initialized")
    return {"status": "healthy", "records_loaded": len(names_repo)}

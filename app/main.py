from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, HTTPException, Query

from app.repositories.names import NamesRepository
from app.services.normalizer import normalize
from app.services.similarity import calculate_similarity

names_repo: NamesRepository | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load data on startup."""
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
    """
    Search for similar names in the database.

    Returns a JSON where the key is the record ID and the value contains
    the found name and its similarity percentage, sorted by similarity (descending).

    Performance tip: use_blocking=True reduces comparisons significantly for large datasets.
    """
    if names_repo is None:
        raise HTTPException(status_code=503, detail="Service not initialized")

    results = []

    if use_blocking:
        candidates = names_repo.candidates_for(name)
    else:
        candidates = list(names_repo)

    for record_id, db_name in candidates:
        similarity = calculate_similarity(name, db_name)
        if similarity >= threshold:
            results.append((record_id, db_name, similarity))

    # Sort by similarity descending and apply limit
    results.sort(key=lambda x: x[2], reverse=True)
    results = results[:limit]

    # Format output as requested: {id: {name, similarity}}
    return {
        str(record_id): {"name": db_name, "similarity": round(similarity, 2)}
        for record_id, db_name, similarity in results
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    if names_repo is None:
        raise HTTPException(status_code=503, detail="Service not initialized")
    return {"status": "healthy", "records_loaded": len(names_repo)}

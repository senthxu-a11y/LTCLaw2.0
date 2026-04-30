from fastapi import APIRouter


router = APIRouter(prefix="/game-knowledge-base", tags=["game-knowledge-base"])


@router.get("/entries")
async def list_entries() -> dict[str, list[dict[str, str]]]:
    return {"items": []}

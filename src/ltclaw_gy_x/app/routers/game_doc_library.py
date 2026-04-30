from fastapi import APIRouter


router = APIRouter(prefix="/game-doc-library", tags=["game-doc-library"])


@router.get("/documents")
async def list_documents() -> dict[str, list[dict[str, str]]]:
    return {"items": []}

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List
from services.stats_fetcher import get_stats

router = APIRouter(
    prefix="/api/visual-by-graph",
    tags=["Visual By Graph"]
)

class URLRequest(BaseModel):
    urls: List[str]

@router.post("/")
async def get_visual_stats_batch(request: URLRequest):
    """
    Accepts a list of social media URLs.
    Returns a JSON array containing the stat dictionaries for all requested videos.
    """
    if not request.urls:
        raise HTTPException(status_code=400, detail="No URLs provided.")
        
    results = [get_stats(url) for url in request.urls]
    return results

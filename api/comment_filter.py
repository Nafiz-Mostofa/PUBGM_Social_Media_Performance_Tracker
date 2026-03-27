from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from services.youtube_service import get_youtube_comments, get_youtube_stats, extract_video_id, get_api_key
from services.nlp_service import analyze_comment_topics

router = APIRouter(
    prefix="/api/comment-filter",
    tags=["Comment Filter"]
)


class SingleURLRequest(BaseModel):
    url: str


@router.post("/")
async def get_raw_comments(request: SingleURLRequest):
    """
    Fetches raw comments for a given URL and performs topic analysis.
    Supports YouTube, Facebook, and TikTok.
    """
    # Check for multiple links
    url_stripped = request.url.strip()
    if " " in url_stripped or "," in url_stripped or "\n" in url_stripped:
        raise HTTPException(status_code=400, detail="Input only one link")

    url_lower = url_stripped.lower()
    raw_data = None

    # Step 1: Fetch raw comments using existing logic
    if "youtube.com" in url_lower or "youtu.be" in url_lower:
        raw_data = get_youtube_comments(request.url)
    elif any(p in url_lower for p in ["facebook.com", "fb.watch", "instagram.com", "tiktok.com", "vt.tiktok"]):
        raise HTTPException(status_code=400, detail="Only Available for youtube videos Link")
    # FB/TikTok/IG removed for comment filter as per request
    
    # Initialize default if no scraper matches
    if not raw_data:
        raw_data = {
            "total_comments_available": "0",
            "fetched_comments_count": 0,
            "comments": []
        }

    # Step 2: Extract extracted comments and pass to the NLP function
    comments_list = raw_data.get("comments", [])
    
    # Wait for semantic topic analysis from Groq (Llama 3)
    # Ensure GROQ_API_KEY is set in your environment
    topic_analysis = await analyze_comment_topics(comments_list)

    # Step 3: Combine findings into the specified JSON structure
    return {
        "total_comments_available": str(raw_data.get("total_comments_available", "0")),
        "fetched_comments_count": raw_data.get("fetched_comments_count", 0),
        "topic_analysis": topic_analysis,
        "comments": comments_list
    }


from .youtube_service import get_youtube_stats
from .facebook_service import get_facebook_stats
from .instagram_service import get_instagram_stats
from .tiktok_service import get_tiktok_stats

def get_stats(url: str) -> dict:
    """
    Centralized function to fetch stats based on the platform identified by the URL.
    Supports YouTube, Facebook, Instagram, and TikTok.
    """
    url_lower = url.lower()
    
    if "youtube.com" in url_lower or "youtu.be" in url_lower:
        return get_youtube_stats(url)
    elif "facebook.com" in url_lower or "fb.watch" in url_lower:
        return get_facebook_stats(url)
    elif "instagram.com" in url_lower:
        return get_instagram_stats(url)
    elif "tiktok.com" in url_lower:
        return get_tiktok_stats(url)
    else:
        return {
            "url": url,
            "error": "Unsupported platform. Please provide a YouTube, Facebook, Instagram, or TikTok URL."
        }

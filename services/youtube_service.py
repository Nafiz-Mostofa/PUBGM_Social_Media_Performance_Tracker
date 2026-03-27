import requests
import re
import os

# API Key will be read dynamically from the environment initialized at main.py startup.
def get_api_key():
    return os.getenv("YOUTUBE_API_KEY")

def extract_video_id(url: str) -> str:
    """
    Extracts the YouTube video ID from a given URL.
    Handles standard watch URLs and short youtu.be URLs.
    """
    pattern = r"(?:v=|\/)([0-9A-Za-z_-]{11}).*"
    match = re.search(pattern, url)
    
    if match:
        return match.group(1)
    return None

def get_youtube_stats(url: str) -> dict:
    """
    Fetches viewCount, likeCount, and commentCount for a given YouTube video URL.
    Returns the exact extracted data as a dictionary.
    """
    video_id = extract_video_id(url)
    if not video_id:
        return {"error": "Could not extract a valid Video ID from the provided URL."}

    api_url = "https://www.googleapis.com/youtube/v3/videos"
    
    params = {
        "part": "statistics",  
        "id": video_id,        
        "key": get_api_key()         
    }
    
    try:
        response = requests.get(api_url, params=params)
        response.raise_for_status() 
        
        data = response.json()
        
        if not data.get("items"):
            return {"error": "Could not find video statistics. Please check the Video URL."}
            
        stats = data["items"][0]["statistics"]
        
        # We try to get metrics, default to 0 if they are hidden
        views = stats.get("viewCount", 0)
        likes = stats.get("likeCount", 0)
        comments = stats.get("commentCount", 0)
        
        return {
            "platform": "youtube",
            "url": url,
            "video_id": video_id,
            "views": int(views) if views else 0,
            "likes": int(likes) if likes else 0,
            "comments": int(comments) if comments else 0
        }
        
    except requests.exceptions.RequestException as e:
        error_msg = str(e)
        # Fix: Check response existence before accessing status_code
        if 'response' in locals() and response is not None and response.status_code in [400, 403]:
            error_msg += " - Hint: This is often caused by an invalid or missing API Key."
        return {
            "platform": "youtube",
            "url": url,
            "error": error_msg
        }

def get_youtube_comments(url: str, max_results: int = 100) -> dict:
    """
    Fetches raw comments for a given YouTube video URL using the YouTube Data API v3.
    Returns a dictionary with metadata and the list of comments.
    """
    video_id = extract_video_id(url)
    if not video_id:
        return {
            "total_comments_available": "0",
            "fetched_comments_count": 0,
            "comments": []
        }

    # 1. Fetch Total Available Comments
    total_comments_available = "0"
    try:
        stats_url = "https://www.googleapis.com/youtube/v3/videos"
        s_params = {
            "part": "statistics",
            "id": video_id,
            "key": get_api_key()
        }
        s_res = requests.get(stats_url, params=s_params)
        s_data = s_res.json()
        if s_data.get("items"):
            total_comments_available = s_data["items"][0]["statistics"].get("commentCount", "0")
    except Exception:
        pass

    # 2. Fetch Comments List
    api_url = "https://www.googleapis.com/youtube/v3/commentThreads"
    comments = []
    next_page_token = None

    while len(comments) < max_results:
        batch_size = min(100, max_results - len(comments))
        
        params = {
            "part": "snippet,replies",
            "videoId": video_id,
            "maxResults": batch_size,
            "key": get_api_key()
        }
        if next_page_token:
            params["pageToken"] = next_page_token

        try:
            response = requests.get(api_url, params=params)
            
            if response.status_code == 403:
                error_data = response.json().get("error", {})
                for error in error_data.get("errors", []):
                    if error.get("reason") == "commentsDisabled":
                        break
            
            response.raise_for_status()
            data = response.json()
            
            items = data.get("items", [])
            for item in items:
                if len(comments) >= max_results:
                    break
                
                snippet = item["snippet"]["topLevelComment"]["snippet"]
                comments.append({
                    "author": snippet.get("authorDisplayName", "Unknown"),
                    "text": snippet.get("textDisplay", ""),
                    "platform": "youtube"
                })
                
                replies = item.get("replies", {}).get("comments", [])
                for reply in replies:
                    if len(comments) >= max_results:
                        break
                    reply_snippet = reply["snippet"]
                    comments.append({
                        "author": reply_snippet.get("authorDisplayName", "Unknown"),
                        "text": reply_snippet.get("textDisplay", ""),
                        "platform": "youtube"
                    })
            
            next_page_token = data.get("nextPageToken")
            if not next_page_token:
                break
                
        except Exception:
            break

    return {
        "total_comments_available": total_comments_available,
        "fetched_comments_count": len(comments),
        "comments": comments
    }

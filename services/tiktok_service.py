import os
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from .webdriver_utils import create_driver, inject_cookies, parse_number_string

def get_tiktok_stats(url: str) -> dict:
    """
    Scrapes a TikTok video URL for views, likes, comments, shares, and saves.
    Uses .env Cookie injection and fresh temporary browser instances.

    Required .env variable:
    TT_SESSION_COOKIE="sessionid=...; tt_webid_v2=..."
    """
    driver = None
    views, likes, comments, shares, saves = 0, 0, 0, 0, 0
    
    try:
        driver = create_driver()
        
        # 1. Navigate to TikTok domain first to allow cookie injection
        driver.get("https://www.tiktok.com")
        time.sleep(1)
        
        # 2. Inject Cookies from .env
        tt_cookie = os.getenv('TT_SESSION_COOKIE', '')
        if tt_cookie:
            inject_cookies(driver, tt_cookie, ".tiktok.com")
            
        # 3. Navigate to the target URL
        driver.get(url)
        
        # 4. Wait for the page to load and metrics to appear
        try:
            WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, '[data-e2e="browse-video"], [data-e2e="video-player"]'))
            )
        except Exception:
            time.sleep(2)

        # 5. Extraction logic with robust try-except for each metric
        
        # Views (often in meta tags or specific data attributes)
        try:
            # Try to find view count in page source JSON first
            import re
            page_source = driver.page_source
            v_m = re.search(r'"playCount":(\d+)', page_source) or re.search(r'"video_view_count":(\d+)', page_source)
            if v_m:
                views = int(v_m.group(1))
            else:
                # Fallback to UI element if any
                view_element = driver.find_element(By.CSS_SELECTOR, '[data-e2e="view-count"]')
                views = parse_number_string(view_element.text)
        except Exception:
            pass
            
        # Likes
        try:
            element = driver.find_element(By.CSS_SELECTOR, '[data-e2e="like-count"]')
            likes = parse_number_string(element.text)
        except Exception:
            pass
            
        # Comments
        try:
            element = driver.find_element(By.CSS_SELECTOR, '[data-e2e="comment-count"]')
            comments = parse_number_string(element.text)
        except Exception:
            pass
            
        # Shares
        try:
            element = driver.find_element(By.CSS_SELECTOR, '[data-e2e="share-count"]')
            shares = parse_number_string(element.text)
        except Exception:
            pass
            
        # Saves (Favorites)
        try:
            candidates = ['[data-e2e="undefined-count"]', '[data-e2e="favorite-count"]']
            for selector in candidates:
                try:
                    element = driver.find_element(By.CSS_SELECTOR, selector)
                    if element.text:
                        saves = parse_number_string(element.text)
                        if saves > 0:
                            break
                except Exception:
                    continue
        except Exception:
            pass

        return {
            "platform": "tiktok",
            "url": url,
            "views": views,
            "likes": likes,
            "comments": comments,
            "shares": shares,
            "saves": saves
        }

    except Exception as e:
        return {
            "platform": "tiktok",
            "url": url,
            "views": 0,
            "likes": 0,
            "comments": 0,
            "shares": 0,
            "saves": 0,
            "error": str(e)
        }


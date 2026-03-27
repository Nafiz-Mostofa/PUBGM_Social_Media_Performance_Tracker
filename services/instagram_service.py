import os
import time
import re
import json
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from .webdriver_utils import create_driver, inject_cookies, parse_number_string


def _extract_shortcode(url: str) -> str:
    """Extract the post/reel shortcode from an Instagram URL."""
    match = re.search(r'(?:reel|p|tv)/([A-Za-z0-9_-]+)', url)
    return match.group(1) if match else ""

# ─── Main Scraper ─────────────────────────────────────────────────────────────
def get_instagram_stats(url: str) -> dict:
    """
    Scrapes an Instagram post/reel URL for likes, comments, shares, and views.
    Uses .env Cookie injection and fresh temporary browser instances for cloud servers.
    
    Required .env variable:
    IG_SESSION_COOKIE="sessionid=123456789%3Aabcdef%3A123; ds_user_id=12345"
    """
    likes = 0
    comments = 0
    shares = 0
    views = 0

    driver = None
    try:
        driver = create_driver()
        
        # 1. Pre-navigate to the domain to allow cookie injection
        driver.get("https://www.instagram.com")
        
        # 2. Inject Cookies from .env
        ig_cookie = os.environ.get('IG_SESSION_COOKIE', '')
        inject_cookies(driver, ig_cookie, ".instagram.com")
        
        shortcode = _extract_shortcode(url)

        # ── STRATEGY 1 (PRIMARY): Direct GraphQL API call ──────────────
        # This is the ONLY reliable per-post source. HTML page parsing is unreliable 
        # because Instagram injects Suggested Posts on the same page, and any `max()`
        # approach will accidentally pick up their higher like/comment counts.
        if shortcode:
            try:
                gql_url = f'https://www.instagram.com/graphql/query/?doc_id=10015901848480474&variables={{"shortcode":"{shortcode}"}}'
                driver.get(gql_url)
                
                try:
                    WebDriverWait(driver, 5).until(
                        EC.presence_of_element_located((By.TAG_NAME, "pre"))
                    )
                    raw = driver.find_element(By.TAG_NAME, "pre").text
                except Exception:
                    raw = driver.find_element(By.TAG_NAME, "body").text
                
                data = json.loads(raw)
                media = data.get('data', {}).get('xdt_shortcode_media', {})
                if media:
                    # Likes — from the preview like edge
                    edge_likes = media.get('edge_media_preview_like', {})
                    if edge_likes and edge_likes.get('count') is not None:
                        likes = int(edge_likes['count'])
                    elif media.get('like_count') is not None:
                        likes = int(media['like_count'])
                    
                    # Comments — from edge_media_to_comment
                    edge_comments = media.get('edge_media_to_comment', {})
                    if edge_comments and edge_comments.get('count') is not None:
                        comments = int(edge_comments['count'])
                    elif media.get('comment_count') is not None:
                        comments = int(media['comment_count'])
                    
                    # Shares
                    if media.get('share_count') is not None:
                        shares = int(media['share_count'])
                    
                    # Views: only for reels/video content
                    is_reel = any(kw in url.lower() for kw in ['/reel/', '/tv/', '/v/'])
                    if is_reel:
                        # Priority: video_play_count (app-shown plays) > play_count > video_view_count
                        vpc = media.get('video_play_count')
                        pc = media.get('play_count')
                        vvc = media.get('video_view_count')
                        if vpc is not None:
                            views = int(vpc)
                        elif pc is not None:
                            views = int(pc)
                        elif vvc is not None:
                            views = int(vvc)
            except Exception:
                pass

        # ── STRATEGY 2 (FALLBACK): Navigate to post and parse page source ──
        # Only triggered if GraphQL returned nothing (blocked, rate-limited, etc.)
        if likes == 0 and comments == 0:
            driver.get(url)
            try:
                WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.TAG_NAME, "article"))
                )
            except Exception:
                time.sleep(2)
            
            page_source = driver.page_source

            # Try HTML JSON blobs anchored to the shortcode (first match only, no max)
            if shortcode:
                scripts = re.findall(r'<script type="application/json"[^>]*>(.*?)</script>', page_source, re.DOTALL)
                for script in scripts:
                    if shortcode in script:
                        if 'xdt_api__v1__media__shortcode__web_info' in script or f'"code":"{shortcode}"' in script:
                            likes_match = re.search(r'"like_count"\s*:\s*(\d+)', script)
                            comments_match = re.search(r'"comment_count"\s*:\s*(\d+)', script)
                            shares_match = re.search(r'"share_count"\s*:\s*(\d+)', script)
                            views_match = (
                                re.search(r'"video_play_count"\s*:\s*(\d+)', script) or
                                re.search(r'"play_count"\s*:\s*(\d+)', script) or
                                re.search(r'"video_view_count"\s*:\s*(\d+)', script)
                            )
                            # Use first match only — do NOT use max() to avoid suggested post contamination
                            if likes_match: likes = int(likes_match.group(1))
                            if comments_match: comments = int(comments_match.group(1))
                            if shares_match: shares = int(shares_match.group(1))
                            if views_match: views = int(views_match.group(1))
                            if likes > 0 or comments > 0:
                                break

            # Body text last-resort for likes and comments
            if likes == 0 and comments == 0:
                try:
                    body_text = driver.find_element(By.TAG_NAME, "body").text
                    lines = [l.strip() for l in body_text.strip().split('\n') if l.strip()]
                    for i in range(len(lines) - 1, 0, -1):
                        is_date = bool(re.match(
                            r'^\d{1,2}\s+(?:january|february|march|april|may|june|july|august|september|october|november|december|'
                            r'jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec|d|w|h|m|mo)\b',
                            lines[i].lower()
                        ))
                        if is_date and i >= 2:
                            comment_line = lines[i - 1]
                            like_line = lines[i - 2]
                            if re.match(r'^[\d,KMB.]+$', comment_line, re.IGNORECASE) and \
                               re.match(r'^[\d,KMB.]+$', like_line, re.IGNORECASE):
                                likes = parse_number_string(like_line)
                                comments = parse_number_string(comment_line)
                                break
                except Exception:
                    pass

        return {
            "platform": "instagram",
            "url": url,
            "likes": likes,
            "comments": comments,
            "shares": shares,
            "views": views
        }
    except Exception as e:
        return {
            "platform": "instagram",
            "url": url,
            "likes": 0,
            "comments": 0,
            "shares": 0,
            "views": 0,
            "error": str(e)
        }
    finally:
        # Guarantee closure of the WebDriver session to prevent server memory leaks
        if driver is not None:
            try:
                driver.quit()
            except Exception:
                pass





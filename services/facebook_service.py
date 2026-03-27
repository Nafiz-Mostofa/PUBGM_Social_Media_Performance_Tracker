import os
import time
import re
from .webdriver_utils import create_driver, inject_cookies, parse_number_string


def get_facebook_stats(url: str) -> dict:
    """
    Scrapes a Facebook post/reel URL for likes, comments, shares, and views.
    Uses .env Cookie injection and fresh temporary browser instances.

    Required .env variable:
    FB_SESSION_COOKIE="c_user=12345; xs=ABCDEF; datr=XYZ..."
    """
    driver = None
    try:
        driver = create_driver()
        fb_cookie = os.environ.get('FB_SESSION_COOKIE', '')

        reel_keywords = ['/reel/', '/watch/',
                         '/share/v/', '/videos/', '/share/r/']

        # 1. Navigate directly — /share/r/ reel links are public and load without login.
        driver.get(url)
        time.sleep(2)

        body_text = driver.find_element("tag name", "body").text
        page_lower = body_text.lower()
        landed_url = driver.current_url.lower()

        # CRITICAL: Save the initial page source before any cookie retry.
        # Facebook serves og:title with metrics ("48M views · 284K reactions") on the
        # gated overlay page. A failed cookie retry navigates away and loses this source.
        initial_page_source = driver.page_source

        # 2. Detect gated/login page and retry with session cookies.
        is_gated = (
            'login' in landed_url or
            '/checkpoint/' in landed_url or
            ('log in' in page_lower and 'create new account' in page_lower) or
            ('log in' in page_lower and 'sign up' in page_lower)
        )

        if is_gated and fb_cookie:
            driver.get("https://www.facebook.com")
            inject_cookies(driver, fb_cookie, ".facebook.com")
            driver.get(url)
            time.sleep(2)
            new_body = driver.find_element("tag name", "body").text
            new_lower = new_body.lower()

            # Only adopt the retry result if it kept reel content (valid cookies).
            # Expired cookies redirect to a pure login page — we'd lose the stacked
            # numbers (284K / 8.2K / 4.3K) that were visible in the initial overlay.
            retry_kept_content = (
                'public' in new_lower and (
                    'reels' in new_lower or
                    'see more on facebook' in new_lower or
                    'comments' in new_lower
                )
            )
            if retry_kept_content:
                body_text = new_body
                page_lower = new_lower
                landed_url = driver.current_url.lower()
            # else: keep initial body_text — expired-cookie retry gave a worse page

        # Page source for JSON/meta strategies.
        # Prefer current (may have more data if cookies worked).
        # Fall back to initial if current no longer has the reel's og:title.
        page_source = driver.page_source
        final_url = driver.current_url

        is_reel = any(kw in url.lower() for kw in reel_keywords) or \
            any(kw in final_url.lower() for kw in reel_keywords)

        likes, comments, shares, views = 0, 0, 0, 0
        lines = [l.strip() for l in body_text.strip().split('\n') if l.strip()]

        # ── Strategy 0: og:title meta tag (most reliable for reels) ──────────────
        # Try current page_source first, then fall back to initial_page_source.
        for source in [page_source, initial_page_source]:
            og_title_match = re.search(
                r'<meta[^>]+property=["\']og:title["\'][^>]+content=["\']([^"\']*)["\']|'
                r'<meta[^>]+content=["\']([^"\']*)["\'][^>]+property=["\']og:title["\']',
                source, re.IGNORECASE
            )
            if og_title_match:
                title_val = (og_title_match.group(
                    1) or og_title_match.group(2) or '')
                title_val = title_val.replace('&amp;', '&').replace(
                    '&#039;', "'").replace('&quot;', '"')
                if title_val:
                    # Extract reactions/likes (e.g. "3.3K reactions")
                    l_m = re.search(
                        r'([\d,.km]+)\s*(?:reactions?|likes?)', title_val, re.IGNORECASE)
                    if l_m and likes == 0:
                        likes = parse_number_string(l_m.group(1))

                    # Extract views — only for reels (e.g. "48K views" or "1.2M plays")
                    if is_reel and views == 0:
                        v_m = re.search(
                            r'([\d,.km]+)\s*(?:views?|plays?)', title_val, re.IGNORECASE)
                        if v_m:
                            views = parse_number_string(v_m.group(1))

            # If we found views (primary goal), we can stop searching sources.
            if views > 0:
                break

        # ── Strategy 0b: Page source JSON for views (reel only) ───────────────────
        if is_reel and views == 0:
            # Check for raw numbers first
            for pattern in [
                r'"video_view_count"\s*:\s*"?(\d+)"?',
                r'"play_count"\s*:\s*"?(\d+)"?',
                r'"view_count"\s*:\s*"?(\d+)"?',
                r'"playCount"\s*:\s*"?(\d+)"?',
                r'"viewCount"\s*:\s*"?(\d+)"?',
            ]:
                m = re.search(pattern, page_source, re.IGNORECASE)
                if m and int(m.group(1)) > 0:
                    views = int(m.group(1))
                    break

            # Fallback to suffixed numbers in JSON (e.g. "play_count_text":"48M")
            if views == 0:
                for pattern in [
                    r'"play_count_text"\s*:\s*"([\d,km.]+)"',
                    r'"view_count_text"\s*:\s*"([\d,km.]+)"',
                ]:
                    m = re.search(pattern, page_source, re.IGNORECASE)
                    if m:
                        views = parse_number_string(m.group(1))
                        if views > 0:
                            break

        # ── Strategy 0c: Page source JSON for shares ──────────────────────────────
        if shares == 0:
            for pattern in [r'"share_count"\s*:\s*"?(\d+)"?', r'"shares"\s*:\s*"?(\d+)"?']:
                m = re.search(pattern, page_source, re.IGNORECASE)
                if m and int(m.group(1)) > 0:
                    shares = int(m.group(1))
                    break

        # ── Strategies 1-5: Body text fallback (for any values still missing) ─────
        def find_all_metrics(patterns, text):
            matches = []
            for p in patterns:
                for m in re.finditer(p, text, re.IGNORECASE):
                    val = parse_number_string(m.group(1))
                    matches.append((val, m.start()))
            return matches

        if likes == 0 or comments == 0 or shares == 0:
            l_candidates = find_all_metrics([
                r'(?:all reactions:|reactions:|likes:)\s*([\d,km.]+)',
                r'([\d,km.]+)\s*(?:likes|reactions)',
                r'reactions\s*([\d,km.]+)'
            ], body_text)

            c_candidates = find_all_metrics([
                r'(?:all comments:|comments:)\s*([\d,km.]+)',
                r'([\d,km.]+)\s*comments?',
                r'comments\s*([\d,km.]+)'
            ], body_text)

            s_candidates = find_all_metrics([
                r'(?:all shares:|shares:)\s*([\d,km.]+)',
                r'([\d,km.]+)\s*shares?',
                r'shares\s*([\d,km.]+)'
            ], body_text)

            if l_candidates:
                l_candidates.sort(key=lambda x: x[0], reverse=True)
                if likes == 0:
                    likes, best_l_pos = l_candidates[0]
                else:
                    best_l_pos = l_candidates[0][1]

                if comments == 0 and c_candidates:
                    c_candidates.sort(key=lambda x: abs(x[1] - best_l_pos))
                    comments = c_candidates[0][0]
                if shares == 0 and s_candidates:
                    s_candidates.sort(key=lambda x: abs(x[1] - best_l_pos))
                    shares = s_candidates[0][0]
            else:
                if likes == 0 and comments == 0 and shares == 0:
                    if c_candidates:
                        comments = c_candidates[0][0]
                    if s_candidates:
                        shares = s_candidates[0][0]

            # ── Strategy 2: Bare likes fallback ──
            if likes == 0 and (comments > 0 or shares > 0):
                bare_likes = re.search(
                    r'([\d,km.]+)\n[\d,km.]+\s*comments?', page_lower)
                if bare_likes:
                    likes = parse_number_string(bare_likes.group(1))

            # ── Strategy 3: Standalone number before comments (Reel-style unlabeled likes) ──
            if likes == 0 and comments > 0:
                c_match = re.search(
                    r'([\d,km.]+)\s*comments?', body_text, re.IGNORECASE)
                if c_match:
                    before_lines = [
                        l.strip() for l in body_text[:c_match.start()].split('\n') if l.strip()]
                    for line in reversed(before_lines[-5:]):
                        if re.match(r'^[\d,km.]+$', line, re.IGNORECASE):
                            likes = parse_number_string(line)
                            break

            # ── Strategy 4: Reels stacked-number layout after "Public" ──────────
            # Body text for a public reel (with or without login overlay) is:
            #   Public / 3.4K / 40 / 68 / Reels / See more on Facebook
            # Run whenever any engagement metric is still missing.
            if likes == 0 or comments == 0 or shares == 0:
                for i, line in enumerate(lines):
                    if re.match(r'^[\d,km.]+$', line, re.IGNORECASE):
                        if i > 0 and lines[i-1].lower() in ('public', 'reels', 'see more on facebook'):
                            if likes == 0:
                                likes = parse_number_string(line)
                            j = i + 1
                            if j < len(lines) and re.match(r'^[\d,km.]+$', lines[j], re.IGNORECASE):
                                if comments == 0:
                                    comments = parse_number_string(lines[j])
                                j += 1
                                if j < len(lines) and re.match(r'^[\d,km.]+$', lines[j], re.IGNORECASE):
                                    if shares == 0:
                                        shares = parse_number_string(lines[j])
                            break

            # ── Strategy 5: Reels/Video stacked-number layout ──
            if likes == 0 and comments == 0:
                for i, line in enumerate(lines):
                    low = line.lower()
                    if low in ('public', 'reels', 'see more on facebook'):
                        continue
                    if re.match(r'^[\d,km.]+$', line, re.IGNORECASE):
                        num_start = i
                        num_lines = []
                        for j in range(i, min(i + 5, len(lines))):
                            if re.match(r'^[\d,km.]+$', lines[j], re.IGNORECASE):
                                num_lines.append(lines[j])
                            else:
                                break
                        prev_line = lines[num_start -
                                          1].lower() if num_start > 0 else ""
                        after_idx = num_start + len(num_lines)
                        next_line = lines[after_idx].lower(
                        ) if after_idx < len(lines) else ""
                        is_anchored = prev_line in ('public', 'friends', 'only me') or \
                            next_line in ('reels', 'see more on facebook')
                        if is_anchored and len(num_lines) >= 2:
                            if likes == 0:
                                likes = parse_number_string(num_lines[0])
                            if comments == 0:
                                comments = parse_number_string(num_lines[1])
                            if shares == 0 and len(num_lines) >= 3:
                                shares = parse_number_string(num_lines[2])
                            break

        # ── Views body text fallback (reel only) ──────────────────────────────────
        if is_reel and views == 0:
            # Use a broad pattern — allow any non-alphanumeric char between number and "views" or "plays"
            views_match = re.search(
                r'([\d,.km]+)[^\w]*(?:views?|plays?)', page_lower, re.IGNORECASE)
            if views_match:
                views = parse_number_string(views_match.group(1))

        return {
            "platform": "facebook",
            "url": url,
            "likes": likes,
            "comments": comments,
            "shares": shares,
            "views": views
        }
    except Exception as e:
        return {
            "platform": "facebook",
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






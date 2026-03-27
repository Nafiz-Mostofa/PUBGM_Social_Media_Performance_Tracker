import os
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options

_chromedriver_path = None


def get_chromedriver_path():
    """Cache the chromedriver path so webdriver_manager doesn't re-check on every call."""
    global _chromedriver_path
    if _chromedriver_path is None:
        _chromedriver_path = ChromeDriverManager().install()
    return _chromedriver_path


def create_driver():
    """Creates a fresh, anonymous, headless Chrome WebDriver instance for production."""
    options = Options()
    options.page_load_strategy = 'eager'
    if os.getenv('DEBUG_FACEBOOK', '0') != '1':
        options.add_argument("--headless=new")
    else:
        print("[DEBUG] HEADLESS=false - Chrome will open for FB debugging")
        options.add_argument("--start-maximized")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")

    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    
    # Add realistic user agent to avoid basic blocks
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36")
    
    options.add_experimental_option(
        "prefs", {
            "profile.managed_default_content_settings.images": 2,
            "profile.default_content_setting_values.notifications": 2
        })

    service = Service(get_chromedriver_path())
    driver = webdriver.Chrome(service=service, options=options)
    return driver


def inject_cookies(driver, cookie_string, domain):
    """Parses a standard raw cookie string and injects it into the Selenium driver."""
    if not cookie_string:
        return

    pairs = cookie_string.split(";")
    for pair in pairs:
        pair = pair.strip()
        if "=" in pair:
            key, val = pair.split("=", 1)
            driver.add_cookie({
                "name": key.strip(),
                "value": val.strip(),
                "domain": domain
            })


def parse_number_string(s: str) -> int:
    """Parses strings like '1.2K', '500', '1M', '1.2B' into integers."""
    if not s:
        return 0
    s = s.upper().replace(',', '').strip()
    multiplier = 1
    if 'K' in s:
        multiplier = 1000
        s = s.replace('K', '')
    elif 'M' in s:
        multiplier = 1000000
        s = s.replace('M', '')
    elif 'B' in s:
        multiplier = 1000000000
        s = s.replace('B', '')
    try:
        return int(float(s) * multiplier)
    except Exception:
        return 0

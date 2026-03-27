# 🎮 PUBGM Social Media Performance Tracker

A comprehensive, high-performance **FastAPI** backend designed to track, scrape, and analyze social media performance across **YouTube, Facebook, Instagram, and TikTok**. 

This system integrates automated web scraping with **State of the Art Large Language Models (LLMs)** via Groq to provide not just metrics, but semantic intelligence through deep topic analysis of audience conversations.

---

## 🌟 Project Overview

This API serves as the engine for tracking the digital footprint of the PUBGM ecosystem. Key capabilities include:

*   **Multi-Platform Stats**: Real-time fetching of Views, Likes, Comments, Shares, and Saves.
*   **Deep Comment Analysis**: Advanced NLP using **Groq (Llama 3.3-70b)** to cluster thousands of comments into semantic themes.
*   **Multilingual Intelligence**: Native support for English, Bengali, and "Banglish" (phonetic Bengali).
*   **Automated Reporting**: Generation of production-ready `.xlsx` reports with formatted data sheets.
*   **Enterprise Security**: JWT-based authentication and secure header management.

---

## 🛠️ Prerequisites

> [!IMPORTANT]
> **Recommended Python Version: 3.12** 🐍
> 
> We strongly recommend using **Python 3.12 (Stable)**. 
> 
> **WARNING:** Avoid using newer pre-release versions (like **Python 3.14**) or very recent releases where pre-built "wheels" (binary packages) for libraries like `pandas` and `bcrypt` may not be available. Using incompatible versions may result in **100% CPU usage** as your system attempts to compile these massive libraries from source, often failing in the process.

*   **Google Chrome & Chromedriver**: Required for Selenium-based scraping (Facebook/TikTok).
*   **API Access**:
    *   **Groq API Key**: For LLM-powered comment analysis.
    *   **YouTube Data API v3 Key**: For official YouTube metric fetching.

---

## 🚀 Getting Started

### 1. Clone & Setup (First-Time Only)
To clone the files directly into your current folder (without creating an extra subfolder), use a dot `.` at the end:

```powershell
git clone <repository-url> .
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
```
> [!TIP]
> If you've already cloned it into a folder and want to move into it: `cd Social_Media_Tracker`

### 2. Configure Environment Variables
Create a file named `.env` in the root directory and populate it with the following keys:

```env
# Frontend Connection
CLIENT_URL="http://localhost:5173"

# AI Configuration (Groq Cloud)
GROQ_API_KEY="your_groq_api_key_here"

# Social Platform Keys
YOUTUBE_API_KEY="your_youtube_v3_api_key"

# Scraping Session Cookies (Crucial for Selenium Scrapers)
# Extract these from your browser's Developer Tools (Network/Application tab)
FB_SESSION_COOKIE="c_user=...; xs=...;"
IG_SESSION_COOKIE="sessionid=...;"
TT_SESSION_COOKIE="sessionid=...; s_v_web_id=...;"

# Internal Auth Configuration
JWT_SECRET_KEY="your_random_64_character_hex_string"
ADMIN_USERNAME="admin@example.gg"
ADMIN_PASSWORD_HASH="your_bcrypt_hashed_password"
```

### 3. Running the Server (Subsequent Runs)
For everyday use, you do not need to install packages again. Simply activate your environment and start the server:

```powershell
.\venv\Scripts\activate
python -m uvicorn main:app --reload
```

### 4. Accessing the API
*   **Base URL**: `http://localhost:8000`
*   **Interactive Documentation (Swagger UI)**: [http://localhost:8000/docs](http://localhost:8000/docs)
    *   *FastAPI provides this out-of-the-box for testing and debugging endpoints.*

---

## ⚠️ Common Errors & Troubleshooting

### 1. PowerShell Script Execution Error
**Error:** `Activate.ps1 cannot be loaded because running scripts is disabled on this system.`
**Solution:** You need to change the execution policy for your user. Run this command in a PowerShell window (Administrator mode recommended):
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### 2. High CPU Usage / Failed Installation of Pandas/Bcrypt
**Error:** Pip gets stuck "Building Wheel for pandas" and CPU usage hits 100%.
**Solution:** This usually happens because you are using a Python version (like 3.14) that is too new for the available pre-built binary packages.
*   **Fix:** Uninstall your current Python version and install **Python 3.12**. This allows `pip` to download the pre-compiled `.whl` files instantly instead of spending hours trying to compile them on your machine.

### 3. Selenium "Session Expired"
**Error:** Scrapers for FB/IG/TT return empty stats or error messages.
**Solution:** Your session cookies in the `.env` file have likely expired. Log into the platform in your browser, copy the fresh cookie string, and update your `.env` file.

### 4. Project Structure: Files are inside a subfolder (e.g., Social_media_Tracker)
**Error:** After cloning, you see a folder like `Social_media_Tracker` and all your code is inside it, but you want it in the main folder.
**Solution:** This happens because of standard `git clone` behavior. 
- **Prevention:** Always clone using a dot at the end: `git clone <url> .`
- **Fix:** If already cloned, move all files from the subfolder to the root and delete the empty subfolder. Our [config.py](config.py) uses dynamic pathing, so it will automatically adjust to the new location.

---
*Built for Data Enthusiasts and Social Media Ninjas.*

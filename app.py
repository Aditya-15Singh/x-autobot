import os
import random
import sqlite3
from datetime import datetime
from fastapi import FastAPI, Request
import uvicorn
import tweepy
import asyncio

# ------------------------
# Twitter Authentication
# ------------------------
# --- ADD THIS BLOCK FOR DEBUGGING ---
print("--- DEBUGGING KEYS ---")
key = os.getenv("X_API_KEY", "KEY NOT FOUND")
secret = os.getenv("X_API_SECRET", "SECRET NOT FOUND")
token = os.getenv("X_ACCESS_TOKEN", "TOKEN NOT FOUND")
token_secret = os.getenv("X_ACCESS_SECRET", "TOKEN SECRET NOT FOUND")

print(f"API Key Starts With: {key[:5]}")
print(f"API Secret Starts With: {secret[:5]}")
print(f"Access Token Starts With: {token[:5]}")
print(f"Access Token Secret Starts With: {token_secret[:5]}")
print("----------------------")
# --- END DEBUGGING BLOCK ---
auth = tweepy.OAuth1UserHandler(
    os.getenv("X_API_KEY"),
    os.getenv("X_API_SECRET"),
    os.getenv("X_ACCESS_TOKEN"),
    os.getenv("X_ACCESS_SECRET")
)
api = tweepy.API(auth)

# ------------------------
# Database for duplicates
# ------------------------
conn = sqlite3.connect("tweets.db")
c = conn.cursor()
c.execute("CREATE TABLE IF NOT EXISTS posts (text TEXT, created TIMESTAMP)")
conn.commit()

# ------------------------
# FastAPI app
# ------------------------
app = FastAPI()

# Control token
CONTROL_TOKEN = os.getenv("CONTROL_TOKEN", "changeme")

# Automation status
AUTOMATION_ON = True

# ------------------------
# Hinglish Tone Templates
# ------------------------
TEMPLATES = {
    "cricket": [
        "India match jeet gyaaa 🔥🇮🇳",
        "Pak abhi bhi soch raha hai... kaise haar gaye 😂",
        "Kya SIX tha yaar! Pure stadium hil gyaaa 💥"
    ],
    "geopolitics": [
        "Bhai scene garam ho gya... India ne clear bol dia 🇮🇳",
        "Yeh khel ab serious ho chuka hai 🔥",
        "Abhi abhi update aaya hai... sab alert rahooo 🚨"
    ],
    "news": [
        "Breaking News aayi hai bhai... {headline}",
        "Yeh dekh lo, aaj ka sabse bada update 👉 {headline}",
        "Abhi abhi samachar: {headline}"
    ],
    "thread": [
        "Thread 🧵: Aaj right wing ka mood kaisa hai 👇",
        "Chalo shuru karte hai aaj ka political roundup 🗞️🧵"
    ]
}

# ------------------------
# Helpers
# ------------------------
def already_posted(text):
    c.execute("SELECT * FROM posts WHERE text = ?", (text,))
    return c.fetchone() is not None

def save_post(text):
    c.execute("INSERT INTO posts VALUES (?, ?)", (text, datetime.now()))
    conn.commit()

def post_tweet(text):
    if not already_posted(text):
        try:
            api.update_status(text)
            save_post(text)
            print("Tweeted:", text)
        except Exception as e:
            print("Error tweeting:", e)

# ------------------------
# Tasks
# ------------------------
async def cricket_task():
    while True:
        if AUTOMATION_ON:
            msg = random.choice(TEMPLATES["cricket"])
            post_tweet(msg)
        await asyncio.sleep(900)  # every 15 min

async def geopolitics_task():
    while True:
        if AUTOMATION_ON:
            msg = random.choice(TEMPLATES["geopolitics"])
            post_tweet(msg)
        await asyncio.sleep(2700)  # every 45 min

async def news_task():
    while True:
        if AUTOMATION_ON:
            headline = "Example headline"  # placeholder, connect RSS later
            msg = random.choice(TEMPLATES["news"]).format(headline=headline)
            post_tweet(msg)
        await asyncio.sleep(1800)  # every 30 min

async def thread_task():
    while True:
        if AUTOMATION_ON:
            msg = random.choice(TEMPLATES["thread"])
            post_tweet(msg)
        await asyncio.sleep(43200)  # every 12 hrs

# ------------------------
# API Routes
# ------------------------
@app.post("/manual/tweet")
async def manual_tweet(request: Request):
    data = await request.json()
    token = request.query_params.get("token")
    if token != CONTROL_TOKEN:
        return {"error": "Unauthorized"}
    text = data.get("text", "")
    post_tweet(text)
    return {"status": "ok", "text": text}

@app.post("/pause")
async def pause(request: Request):
    global AUTOMATION_ON
    token = request.query_params.get("token")
    if token != CONTROL_TOKEN:
        return {"error": "Unauthorized"}
    AUTOMATION_ON = False
    return {"status": "paused"}

@app.post("/resume")
async def resume(request: Request):
    global AUTOMATION_ON
    token = request.query_params.get("token")
    if token != CONTROL_TOKEN:
        return {"error": "Unauthorized"}
    AUTOMATION_ON = True
    return {"status": "resumed"}

@app.get("/health")
async def health():
    return {"status": "running", "automation": AUTOMATION_ON}

# ------------------------
# Startup
# ------------------------
@app.on_event("startup")
async def startup_event():
    asyncio.create_task(cricket_task())
    asyncio.create_task(geopolitics_task())
    asyncio.create_task(news_task())
    asyncio.create_task(thread_task())

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))

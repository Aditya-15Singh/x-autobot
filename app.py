import os
import random
import sqlite3
from datetime import datetime
from fastapi import FastAPI, Request
import uvicorn
import tweepy
import asyncio
import feedparser # <-- New library

# ------------------------
# Twitter Authentication (v2)
# ------------------------
client = tweepy.Client(
    consumer_key=os.getenv("X_API_KEY"),
    consumer_secret=os.getenv("X_API_SECRET"),
    access_token=os.getenv("X_ACCESS_TOKEN"),
    access_token_secret=os.getenv("X_ACCESS_SECRET")
)

# ------------------------
# NEW: RSS Feed URL
# ------------------------
# You can change this link to any RSS feed you prefer.
NEWS_RSS_URL = "https://timesofindia.indiatimes.com/rssfeedstopstories.cms"

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
CONTROL_TOKEN = os.getenv("CONTROL_TOKEN", "changeme")
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
        "Breaking News: {headline}",
        "Yeh dekh lo, aaj ka sabse bada update 👉 {headline}",
        "Headlines Today: {headline}"
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

# NEW function to get live news
def get_latest_headline(rss_url):
    try:
        feed = feedparser.parse(rss_url)
        # Get the title of the very first entry (the newest one)
        latest_headline = feed.entries[0].title
        return latest_headline
    except Exception as e:
        print(f"Error fetching RSS feed: {e}")
        return "Top story of the moment" # Fallback message if RSS fails

def post_tweet(text):
    if not already_posted(text):
        try:
            client.create_tweet(text=text)
            save_post(text)
            print("Tweeted (v2):", text)
        except Exception as e:
            print("Error tweeting:", e)

# ------------------------
# Main Scheduler Task
# ------------------------
async def main_scheduler_task():
    print("Starting main scheduler... will post one tweet every 2 hours.")
    while True:
        if AUTOMATION_ON:
            topic = random.choice(["cricket", "geopolitics", "news"])
            print(f"Timer fired. Selected topic: {topic}")
            
            if topic == "news":
                # Get a LIVE headline instead of a placeholder
                headline = get_latest_headline(NEWS_RSS_URL)
                msg = random.choice(TEMPLATES[topic]).format(headline=headline)
            else:
                msg = random.choice(TEMPLATES[topic])
            
            post_tweet(msg)
        
        await asyncio.sleep(7200)

# ------------------------
# API Routes
# ------------------------
@app.get("/")
async def root():
    return {"status": "ok"}

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
    asyncio.create_task(main_scheduler_task())

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))

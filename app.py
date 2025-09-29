import os
import random
from datetime import datetime
from fastapi import FastAPI, Request
import uvicorn
import tweepy
import asyncio
import feedparser

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
# RSS Feed URL
# ------------------------
NEWS_RSS_URL = "https://timesofindia.indiatimes.com/rssfeedstopstories.cms"

# ------------------------
# In-Memory Cache for Recent Tweets
# ------------------------
recent_tweets = set()

# ------------------------
# FastAPI app
# ------------------------
app = FastAPI()
CONTROL_TOKEN = os.getenv("CONTROL_TOKEN", "changeme")
AUTOMATION_ON = True

# ------------------------
# NEW: Longer, Multi-part Templates
# ------------------------
TEMPLATES = {
    "cricket": {
        "opening": ["Just in from the match:", "Unbelievable cricket today!", "What a showdown between the teams!"],
        "detail": ["The batting display has been absolutely electrifying.", "That bowling spell was a masterclass in pressure and skill.", "The fielding has been top-notch, saving crucial runs."],
        "closing": ["India is on the path to a historic win. 🇮🇳 #Cricket", "This match is going to be a nail-biter until the very end.", "A truly memorable performance by the squad."]
    },
    "geopolitics": {
        "opening": ["Major geopolitical update:", "The international stage is heating up today.", "A significant development on the world stage:"],
        "detail": ["Diplomatic talks have reached a critical point, with all eyes on the outcome.", "This strategic move is set to have major ripple effects across the region.", "Analysts are closely watching the fallout from this important decision."],
        "closing": ["India stands firm and clear on its national interest. #Geopolitics", "The coming days will be crucial for international relations.", "A new chapter in global politics is unfolding before our eyes."]
    },
    "news": [
        "Breaking News: {headline}",
        "Major Update 👉 {headline}",
        "From the Headlines Today: {headline}"
    ]
}

# ------------------------
# Helpers
# ------------------------
def already_posted(text):
    return text in recent_tweets

def save_post(text):
    recent_tweets.add(text)

def get_latest_headline(rss_url):
    try:
        feed = feedparser.parse(rss_url)
        latest_headline = feed.entries[0].title
        return latest_headline
    except Exception as e:
        print(f"Error fetching RSS feed: {e}")
        return "Top story of the moment"

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
            
            msg = ""
            if topic in ["cricket", "geopolitics"]:
                # Build a longer tweet from parts
                opening = random.choice(TEMPLATES[topic]["opening"])
                detail = random.choice(TEMPLATES[topic]["detail"])
                closing = random.choice(TEMPLATES[topic]["closing"])
                msg = f"{opening} {detail} {closing}"
            
            elif topic == "news":
                headline = get_latest_headline(NEWS_RSS_URL)
                msg = random.choice(TEMPLATES[topic]).format(headline=headline)
            
            # Ensure tweet is not too long (X's limit is 280)
            if len(msg) > 280:
                msg = msg[:277] + "..."

            post_tweet(msg)
        
        await asyncio.sleep(7200) # 2 hours

# ------------------------
# API Routes
# ------------------------
@app.get("/")
async def root():
    return {"status": "ok"}

# ... (the rest of the API routes: manual_tweet, pause, resume, health are the same) ...
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
    print("Fetching recent tweets to build memory cache...")
    try:
        me = client.get_me().data
        my_tweets = client.get_users_tweets(me.id, max_results=20).data
        if my_tweets:
            for tweet in my_tweets:
                recent_tweets.add(tweet.text)
        print(f"Memory cache built. Found {len(recent_tweets)} recent tweets.")
    except Exception as e:
        print(f"Could not fetch recent tweets: {e}")

    asyncio.create_task(main_scheduler_task())

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))

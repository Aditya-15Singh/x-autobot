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
# NEW: Improved Hinglish Templates
# ------------------------
TEMPLATES = {
    "cricket": {
        "opening": ["Match ka scene garam hai!", "Yaar, kya zabardast cricket dekhne ko mil raha hai!", "Aaj toh game full power on hai!"],
        "detail": ["Batting line-up form mein lag rahi hai, solid shots maar rahe hain.", "Bowling attack ne toh kamaal kar diya, bilkul pressure bana ke rakha hai.", "Fielding ekdum tight hai, ek-ek run bachana important ho gaya hai."],
        "closing": ["Team India jeet ke taraf badh rahi hai! 🇮🇳 #CricketFever", "End tak suspense bana rahega, pakka!", "Yeh performance saalon tak yaad rakha jayega, historical stuff!"]
    },
    "geopolitics": {
        "opening": ["Bhai, international level pe badi khabar aa rahi hai:", "Duniya mein siyasi hulchul tez ho gayi hai, suno.", "Global stage par ek naya mod aaya hai:"],
        "detail": ["Iss faisle ka asar poore South Asia par padega, sabki nazar ispar hai.", "Deshon ke beech diplomacy ab ek naye level par jaa rahi hai.", "Experts ka kehna hai ki yeh ek strategic masterstroke hai Bharat ki taraf se."],
        "closing": ["Bharat ka stand bilkul clear aur firm hai. #IndiaFirst", "Aane waale din bahut crucial hone waale hain, alert raho.", "Duniya mein power ka balance badal raha hai, dosto."]
    },
    "news": [
        "Abhi abhi ki Breaking News: {headline}",
        "Aaj ki sabse badi khabar 👉 {headline}",
        "Headlines mein aaj: {headline}"
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
        return "desh aur duniya ki khabar"

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
                opening = random.choice(TEMPLATES[topic]["opening"])
                detail = random.choice(TEMPLATES[topic]["detail"])
                closing = random.choice(TEMPLATES[topic]["closing"])
                msg = f"{opening} {detail} {closing}"
            
            elif topic == "news":
                headline = get_latest_headline(NEWS_RSS_URL)
                msg = random.choice(TEMPLATES[topic]).format(headline=headline)
            
            if len(msg) > 280:
                msg = msg[:277] + "..."

            post_tweet(msg)
        
        await asyncio.sleep(7200) # 2 hours

# ------------------------
# API Routes (No changes here)
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
# Startup (No changes here)
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

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
# FINAL: Templates with Hinglish Tone & Hashtags
# ------------------------
TEMPLATES = {
    "cricket": {
        "line1": ["Team India ka jazba hi alag hai!", "Discipline, Strategy, Power - yeh sirf khel nahi, desh ka gaurav hai.", "Rivals can keep trying, but the talent and aggression of our team is unmatched."],
        "line2": ["Yeh naye Bharat ki team hai, joh darna nahi, darana jaanti hai. 💪🇮🇳", "Our boys are making India proud on the world stage.", "Yeh team rukegi nahi, yeh Naya Bharat hai!"],
        "hashtags": ["#TeamIndia", "#CricketFever", "#IndianCricket", "#NayaBharat"]
    },
    "geopolitics": {
        "line1": ["Duniya dekh rahi hai naye Bharat ka dum.", "Our foreign policy is crystal clear: India First.", "Global narratives are changing, and India is at the center of it."],
        "line2": ["No compromises on national security and sovereignty.", "Joh desh ke हित mein hai, wahi hoga. No apologies.", "We will lead, not follow. The world must recognize India's strength."],
        "hashtags": ["#IndiaFirst", "#NationalSecurity", "#SashaktBharat", "#IndianDiplomacy"]
    },
    "news": {
        "templates": ["Desh se badi khabar: {headline}", "Aaj ka sach: {headline}", "Satta ka khel: {headline}"],
        "hashtags": ["#IndiaNews", "#BreakingNews", "#Nationalist"]
    }
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
                line1 = random.choice(TEMPLATES[topic]["line1"])
                line2 = random.choice(TEMPLATES[topic]["line2"])
                msg = f"{line1} {line2}"
            
            elif topic == "news":
                headline = get_latest_headline(NEWS_RSS_URL)
                msg = random.choice(TEMPLATES[topic]["templates"]).format(headline=headline)
            
            # Add 1 or 2 hashtags
            if topic in TEMPLATES and "hashtags" in TEMPLATES[topic]:
                num_hashtags = random.randint(1, 2)
                chosen_hashtags = random.sample(TEMPLATES[topic]["hashtags"], num_hashtags)
                hashtag_string = " ".join(chosen_hashtags)
                
                # Check length and append
                if len(msg) + len(hashtag_string) + 1 <= 280:
                    msg = f"{msg} {hashtag_string}"

            # Final length check
            if len(msg) > 280:
                msg = msg[:277] + "..."

            post_tweet(msg)
        
        await asyncio.sleep(7200)

# ------------------------
# API Routes & Startup (No changes from here down)
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

import os
import random
from fastapi import FastAPI, Request
import uvicorn
import tweepy
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
# FastAPI app
# ------------------------
app = FastAPI()
CONTROL_TOKEN = os.getenv("CONTROL_TOKEN", "changeme")

# ------------------------
# Templates
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
# Helper Functions
# ------------------------
def get_latest_headline(rss_url):
    try:
        feed = feedparser.parse(rss_url)
        return feed.entries[0].title
    except Exception:
        return "desh aur duniya ki khabar"

def post_random_tweet():
    topic = random.choice(["cricket", "geopolitics", "news"])
    print(f"Triggered to post about: {topic}")
    
    msg = ""
    if topic in ["cricket", "geopolitics"]:
        line1 = random.choice(TEMPLATES[topic]["line1"])
        line2 = random.choice(TEMPLATES[topic]["line2"])
        msg = f"{line1} {line2}"
    elif topic == "news":
        headline = get_latest_headline(NEWS_RSS_URL)
        msg = random.choice(TEMPLATES[topic]["templates"]).format(headline=headline)
    
    if topic in TEMPLATES and "hashtags" in TEMPLATES[topic]:
        num_hashtags = random.randint(1, 2)
        chosen_hashtags = random.sample(TEMPLATES[topic]["hashtags"], num_hashtags)
        hashtag_string = " ".join(chosen_hashtags)
        if len(msg) + len(hashtag_string) + 1 <= 280:
            msg = f"{msg} {hashtag_string}"

    try:
        client.create_tweet(text=msg)
        print("Tweeted (v2):", msg)
        return {"status": "success", "tweet": msg}
    except Exception as e:
        print("Error tweeting:", e)
        return {"status": "error", "message": str(e)}

# ------------------------
# API Routes
# ------------------------
@app.get("/")
def root():
    return {"status": "Bot is waiting for a trigger."}

@app.get("/trigger_tweet")
def trigger_tweet(token: str):
    if token != CONTROL_TOKEN:
        return {"error": "Invalid token"}
    result = post_random_tweet()
    return result

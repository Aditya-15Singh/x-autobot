import os
import random
from fastapi import FastAPI, Request
import uvicorn
import tweepy
import feedparser
import requests

# ------------------------
# Webhook for Logging
# ------------------------
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

def log_error_to_webhook(message):
    if WEBHOOK_URL:
        try:
            payload = {'content': f"🚨 **X-AUTOBOT ERROR:**\n```{message}```"}
            requests.post(WEBHOOK_URL, json=payload)
        except Exception as e:
            print(f"Failed to send error to webhook: {e}")

# ------------------------
# CRASH-PROOF CLIENT INITIALIZATION
# ------------------------
# We will now create the client ONLY when it's needed.
def get_tweepy_client():
    try:
        client = tweepy.Client(
            consumer_key=os.getenv("X_API_KEY"),
            consumer_secret=os.getenv("X_API_SECRET"),
            access_token=os.getenv("X_ACCESS_TOKEN"),
            access_token_secret=os.getenv("X_ACCESS_SECRET")
        )
        return client
    except Exception as e:
        error_message = f"CRITICAL: Failed to initialize Tweepy Client. Check API Keys. Error: {e}"
        print(error_message)
        log_error_to_webhook(error_message)
        return None

# ------------------------
# RSS Feed URL & App setup
# ------------------------
NEWS_RSS_URL = "https://timesofindia.indiatimes.com/rssfeedstopstories.cms"
app = FastAPI()
CONTROL_TOKEN = os.getenv("CONTROL_TOKEN", "changeme")

# ... (Templates remain the same) ...
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
    except Exception as e:
        error_message = f"Error fetching RSS feed: {e}"
        print(error_message)
        log_error_to_webhook(error_message)
        return "desh aur duniya ki khabar"

def post_random_tweet():
    client = get_tweepy_client()
    if not client:
        return {"status": "error", "message": "Could not create Twitter client. Check logs."}

    topic = random.choice(["cricket", "geopolitics", "news"])
    print(f"Triggered to post about: {topic}")
    
    msg = ""
    # ... (Message creation logic is the same) ...
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
        error_message = f"Error during tweet creation: {e}"
        print(error_message)
        log_error_to_webhook(error_message)
        return {"status": "error", "message": error_message}

# ------------------------
# API Routes
# ------------------------
@app.get("/")
def root():
    return {"status": "Bot is running and waiting for a trigger."}

@app.get("/trigger_tweet")
def trigger_tweet(token: str):
    if token != CONTROL_TOKEN:
        return {"error": "Invalid token"}
    result = post_random_tweet()
    return result

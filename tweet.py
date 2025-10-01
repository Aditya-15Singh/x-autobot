# tweet.py
import os
import random
import sys
import tweepy
import feedparser

# ------------------------
# CRASH-PROOF CLIENT INITIALIZATION
# ------------------------
def get_tweepy_client():
    try:
        client = tweepy.Client(
            consumer_key=os.getenv("X_API_KEY"),
            consumer_secret=os.getenv("X_API_SECRET"),
            access_token=os.getenv("X_ACCESS_TOKEN"),
            access_token_secret=os.getenv("X_ACCESS_SECRET")
        )
        # optional check: ensure at least one key present
        if not (os.getenv("X_API_KEY") and os.getenv("X_API_SECRET") and os.getenv("X_ACCESS_TOKEN") and os.getenv("X_ACCESS_SECRET")):
            raise RuntimeError("Missing one or more Twitter API environment variables.")
        return client
    except Exception as e:
        print(f"CRITICAL: Failed to initialize Tweepy Client. Error: {e}")
        return None

# ------------------------
# RSS Feed URL & Templates
# ------------------------
NEWS_RSS_URL = os.getenv("NEWS_RSS_URL", "https://timesofindia.indiatimes.com/rssfeedstopstories.cms")

TEMPLATES = {
    "cricket": {
        "line1": [
            "Team India ka jazba hi alag hai!",
            "Discipline, Strategy, Power - yeh sirf khel nahi, desh ka gaurav hai.",
            "Rivals can keep trying, but the talent and aggression of our team is unmatched."
        ],
        "line2": [
            "Yeh naye Bharat ki team hai, joh darna nahi, darana jaanti hai. 💪🇮🇳",
            "Our boys are making India proud on the world stage.",
            "Yeh team rukegi nahi, yeh Naya Bharat hai!"
        ],
        "hashtags": ["#TeamIndia", "#CricketFever", "#IndianCricket", "#NayaBharat"]
    },
    "geopolitics": {
        "line1": [
            "Duniya dekh rahi hai naye Bharat ka dum.",
            "Our foreign policy is crystal clear: India First.",
            "Global narratives are changing, and India is at the center of it."
        ],
        "line2": [
            "No compromises on national security and sovereignty.",
            "Joh desh ke हित mein hai, wahi hoga. No apologies.",
            "We will lead, not follow. The world must recognize India's strength."
        ],
        "hashtags": ["#IndiaFirst", "#NationalSecurity", "#SashaktBharat", "#IndianDiplomacy"]
    },
    "news": {
        "templates": [
            "Desh se badi khabar: {headline}",
            "Aaj ka sach: {headline}",
            "Satta ka khel: {headline}"
        ],
        "hashtags": ["#IndiaNews", "#BreakingNews", "#Nationalist"]
    }
}

# ------------------------
# Helper Functions
# ------------------------
def get_latest_headline(rss_url):
    try:
        feed = feedparser.parse(rss_url)
        if feed.entries and len(feed.entries) > 0:
            return feed.entries[0].title
        return "desh aur duniya ki khabar"
    except Exception as e:
        print(f"Error fetching RSS feed: {e}")
        return "desh aur duniya ki khabar"

def build_message():
    topic = random.choice(["cricket", "geopolitics", "news"])
    print(f"[INFO] Selected topic: {topic}")

    if topic in ["cricket", "geopolitics"]:
        line1 = random.choice(TEMPLATES[topic]["line1"])
        line2 = random.choice(TEMPLATES[topic]["line2"])
        msg = f"{line1} {line2}"
    else:  # news
        headline = get_latest_headline(NEWS_RSS_URL)
        msg = random.choice(TEMPLATES["news"]["templates"]).format(headline=headline)

    # append 1-2 hashtags if room
    if "hashtags" in TEMPLATES[topic]:
        num_hashtags = random.randint(1, 2)
        chosen_hashtags = random.sample(TEMPLATES[topic]["hashtags"], num_hashtags)
        hashtag_string = " ".join(chosen_hashtags)
        if len(msg) + 1 + len(hashtag_string) <= 280:
            msg = f"{msg} {hashtag_string}"

    # final safety trim (should normally not be needed)
    if len(msg) > 280:
        msg = msg[:277] + "..."
    return msg

def post_random_tweet():
    client = get_tweepy_client()
    if not client:
        raise RuntimeError("Could not create Twitter client. Check environment variables.")

    msg = build_message()
    print(f"[INFO] Tweeting: {msg}")

    try:
        client.create_tweet(text=msg)
        print("[SUCCESS] Tweet posted.")
    except Exception as e:
        # Tweepy may return detailed errors — print for logs
        raise RuntimeError(f"Error during tweet creation: {e}")

# ------------------------
# Entrypoint
# ------------------------
if __name__ == "__main__":
    try:
        post_random_tweet()
    except Exception as exc:
        print(f"[ERROR] {exc}")
        # non-zero exit so GitHub Actions shows a failed run and logs error
        sys.exit(1)
    sys.exit(0)

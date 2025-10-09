# tweet.py – India-focused news + aggressive reaction generator (v2 posting)
import os, re, random, sys, requests, tweepy

# --- Tweepy v2 client (required for Essential API) ---
def get_tweepy_client():
    try:
        return tweepy.Client(
            consumer_key=os.getenv("X_API_KEY"),
            consumer_secret=os.getenv("X_API_SECRET"),
            access_token=os.getenv("X_ACCESS_TOKEN"),
            access_token_secret=os.getenv("X_ACCESS_SECRET")
        )
    except Exception as e:
        print("Auth error:", e)
        return None


# --- Fetch Indian headlines via NewsData.io ---
def get_clean_headline():
    try:
        api_key = os.getenv("NEWSDATA_KEY")
        if not api_key:
            return "Missing NewsData API key"

        url = (
            f"https://newsdata.io/api/1/news?"
            f"apikey={api_key}&country=in&language=en&category=top,politics,sports,entertainment"
        )
        r = requests.get(url, timeout=10)
        data = r.json()
        if not data.get("results"):
            return "No latest Indian news available"

        article = random.choice(data["results"][:8])
        title = article.get("title", "").strip()
        desc = article.get("description", "").strip()
        source = article.get("source_id", "NewsData")

        clean_title = re.sub(r"http\S+|www\S+|#\S+|@\S+", "", title)
        snippet = desc[:140] + "…" if len(desc) > 140 else desc
        return f"{clean_title} — {snippet} (via {source.title()})"
    except Exception as e:
        print("API error:", e)
        return "News fetch failed"


# --- Reactions ---
REACTIONS = {
    "cricket": [
        "Rohit Sharma ka form dekh ke lagta hai aggression aur calm dono ek hi insaan mein fit ho gaye hain.",
        "Virat Kohli jab pitch pe aata hai tab crowd ka noise nahi, energy level badh jata hai.",
        "Fans ko sirf win nahi chahiye, domination chahiye — aur yeh squad deliver kar raha hai.",
    ],
    "pakistan": [
        "Pakistan phir se peace ki baat kar raha hai — bhai border pe firing aur mic pe preaching dono ek saath nahi chalte.",
    ],
    "rahul": [
        "Rahul Gandhi ka naya statement aa gaya — bhai lecture kam, leadership zyada dikhado.",
    ],
    "media": [
        "Foreign media ko Bharat ki democracy yaad aa gayi — bhai apne newsroom ke scandals pe kab likhoge?",
    ],
    "movies": [
        "Bollywood fir se experimental mood me — par audience ab content-driven hai boss.",
    ],
    "generic": [
        "Kahani har din nayi, par drama purana — desh ka TRP circus chalu hai.",
        "Aaj ki khabar sun ke laga satire bhi serious lagta hai ab.",
    ],
}


# --- Topic detection ---
def choose_reaction(headline: str) -> str:
    lower = headline.lower()
    if any(w in lower for w in ["cricket", "bcci", "rohit", "kohli", "world cup", "odi", "t20"]):
        return random.choice(REACTIONS["cricket"])
    if "pakistan" in lower:
        return random.choice(REACTIONS["pakistan"])
    if "rahul" in lower or "gandhi" in lower:
        return random.choice(REACTIONS["rahul"])
    if "bbc" in lower or "media" in lower:
        return random.choice(REACTIONS["media"])
    if any(w in lower for w in ["movie", "film", "box office", "bollywood", "cinema", "collection"]):
        return random.choice(REACTIONS["movies"])
    return random.choice(REACTIONS["generic"])


# --- Hashtags ---
HASHTAGS = {
    "cricket": ["#TeamIndia", "#Cricket"],
    "pakistan": ["#IndiaFirst", "#NationalSecurity"],
    "rahul": ["#Politics", "#Bharat"],
    "media": ["#FakeNarrative", "#IndianMedia"],
    "movies": ["#Bollywood", "#IndianCinema"],
    "generic": ["#India", "#Bharat"],
}


# --- Build tweet ---
def build_tweet():
    headline = get_clean_headline()
    reaction = choose_reaction(headline)

    key = "generic"
    lower = headline.lower()
    if any(w in lower for w in ["cricket", "bcci", "rohit", "kohli", "world cup", "odi", "t20"]):
        key = "cricket"
    elif "pakistan" in lower:
        key = "pakistan"
    elif "rahul" in lower or "gandhi" in lower:
        key = "rahul"
    elif "bbc" in lower or "media" in lower:
        key = "media"
    elif any(w in lower for w in ["movie", "film", "box office", "bollywood", "cinema", "collection"]):
        key = "movies"

    tags = " ".join(random.sample(HASHTAGS[key], k=min(2, len(HASHTAGS[key]))))
    tweet = f"{headline} — {reaction} {tags}"
    return tweet[:277] + "..." if len(tweet) > 280 else tweet


# --- Post tweet (v2) ---
def post_tweet():
    client = get_tweepy_client()
    if not client:
        sys.exit("No Tweepy client; check keys.")
    text = build_tweet()
    print("Posting:", text)
    try:
        client.create_tweet(text=text)
        print("✅ Tweet posted successfully (v2).")
    except Exception as e:
        print("Tweet failed:", e)
        sys.exit(1)


if __name__ == "__main__":
    post_tweet()

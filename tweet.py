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
    """Get a current Indian headline with context (NewsData first, ANI fallback)."""
    try:
        key = os.getenv("NEWSDATA_KEY")
        if not key:
            print("❌ Missing NewsData key")
            return "Missing NewsData API key"

        url = (
            f"https://newsdata.io/api/1/news?"
            f"apikey={key}&country=in&language=en&category=top,politics,sports,entertainment,business"
        )

        import requests
        res = requests.get(url, timeout=8)
        if res.status_code != 200:
            print("NewsData fetch failed:", res.status_code)
            raise Exception("NewsData fetch error")

        data = res.json()
        if not data.get("results"):
            print("⚠️ No NewsData results, falling back to ANI")
            raise Exception("empty results")

        # pick a random article that’s not duplicate and has content
        articles = [a for a in data["results"] if a.get("title") and "india" in str(a.get("country", [])).lower()]
        if not articles:
            articles = data["results"]

        article = random.choice(articles[:8])
        title = article.get("title", "").strip()
        source = article.get("source_name", "NewsData")
        snippet = article.get("description") or article.get("content") or ""
        snippet = re.sub(r"\s+", " ", snippet).strip()

        # Clean up
        clean_title = re.sub(r"http\S+|www\S+|#\S+|@\S+", "", title)
       headline = f"{clean_title} — {snippet[:100]}"
        return headline


    except Exception as e:
        print("🟠 Falling back to ANI:", e)
        try:
            import feedparser
            feed = feedparser.parse("https://aniportalimages.blob.core.windows.net/mediafeed/news-feed.xml")
            entry = random.choice(feed.entries[:5])
            return entry.title
        except Exception:
            return "Bharat aur duniya se kuch nayi baatein aa rahi hain"


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
    max_length = 280

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
    elif "supreme court" in lower or "sc " in lower:
        key = "supreme"
    elif "media" in lower or "bbc" in lower:
        key = "media"

    tags_list = HASHTAGS.get(key, HASHTAGS["generic"])
    tags = " ".join(random.sample(tags_list, k=min(2, len(tags_list))))

    base_text = f"{headline} — {reaction}"
    full_tweet = f"{base_text} {tags}".strip()

    if len(full_tweet) > max_length:
        # Try trimming the headline first
        excess = len(full_tweet) - max_length
        if len(headline) > excess + 10:  # leave at least 10 chars
            headline = headline[:len(headline) - excess - 3] + "..."
            base_text = f"{headline} — {reaction}"
            full_tweet = f"{base_text} {tags}".strip()

        # If still too long, trim reaction
        if len(full_tweet) > max_length:
            extra = len(full_tweet) - max_length
            if len(reaction) > extra + 10:
                reaction = reaction[:len(reaction) - extra - 3] + "..."
                base_text = f"{headline} — {reaction}"
                full_tweet = f"{base_text} {tags}".strip()

        # Final safety cut
        if len(full_tweet) > max_length:
            full_tweet = full_tweet[:max_length-3] + "..."

    return full_tweet



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

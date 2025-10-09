# tweet.py – India-focused News + Reaction Autobot (v1.1 posting)

import os, re, random, sys, datetime, requests, feedparser, tweepy
from bs4 import BeautifulSoup


# ------------- CONFIG -------------
ANI_RSS_URL = "https://aniportalimages.blob.core.windows.net/mediafeed/news-feed.xml"


# ------------- TWITTER AUTH (v1.1) -------------
def get_v1_client():
    """Create a Tweepy v1.1 client with OAuth1 (works on free/essential plans)."""
    auth = tweepy.OAuth1UserHandler(
        os.getenv("X_API_KEY"),
        os.getenv("X_API_SECRET"),
        os.getenv("X_ACCESS_TOKEN"),
        os.getenv("X_ACCESS_SECRET")
    )
    return tweepy.API(auth)


# ------------- NEWS FETCH (NewsData.io) -------------
def get_clean_headline():
    """Fetch Indian political, cricket, or movie headlines via NewsData API."""
    try:
        api_key = os.getenv("NEWSDATA_KEY")
        if not api_key:
            return "Missing NewsData API key"

        url = (
            f"https://newsdata.io/api/1/news?"
            f"apikey={api_key}"
            f"&country=in"
            f"&language=en"
            f"&category=top,politics,sports,entertainment"
        )
        r = requests.get(url, timeout=10)
        data = r.json()

        if not data.get("results"):
            return "No latest Indian news available"

        # choose a random recent article
        article = random.choice(data["results"][:8])
        title = article.get("title", "").strip()
        desc = article.get("description", "").strip()
        source = article.get("source_id", "NewsData")

        clean_title = re.sub(r"http\S+|www\S+|#\S+|@\S+", "", title)
        snippet = desc[:140] + "…" if len(desc) > 140 else desc
        headline = f"{clean_title} — {snippet} (via {source.title()})"
        return headline or "India se kuch nayi baatein aayi hain"

    except Exception as e:
        print("API error:", e)
        return "News fetch failed"


# ------------- REACTIONS -------------
REACTIONS = {
    "pakistan": [
        "Pakistan phir se peace ki baat kar raha hai — bhai border pe firing aur mic pe preaching dono ek saath nahi chalte.",
        "Pakistan ko har baar shock lagta hai jab Bharat silence todta hai — yeh diplomacy nahi, warning hai."
    ],
    "rahul": [
        "Rahul Gandhi ka naya statement aa gaya — bhai lecture kam, leadership zyada dikhado.",
        "London se desh chalane ki training phir start? Bharat Zoom pe nahi chalta."
    ],
    "supreme": [
        "Supreme Court ka naya observation aaya — accha hai, bas ground reality bhi kabhi dekh liya karein.",
        "Court se har din lecture milta hai, par ground pe order kab implement hota hai koi nahi poochta."
    ],
    "media": [
        "Foreign media ko Bharat ki democracy yaad aa gayi — bhai apne newsroom ke scandals pe kab likhoge?",
        "BBC aur company ko India par docu banana pasand hai — London ka knife crime kab cover karoge?"
    ],
    "cricket": [
        "Rohit Sharma ka form dekh ke lagta hai aggression aur calm dono ek hi insaan mein fit ho gaye hain.",
        "Virat Kohli jab pitch pe aata hai tab crowd ka noise nahi, energy level badh jata hai.",
        "Team India ka intent clear hai — respect sabko, darr kisi se nahi.",
        "Kohli ke cover drive ko dekhke lagta hai physics optional subject hai.",
        "Fans ko sirf win nahi chahiye, domination chahiye — aur yeh squad deliver kar raha hai.",
        "Commentators keh rahe the old era khatam — bhai Rohit-Virat ne prove kar diya, form temporary hai class permanent.",
        "Ye team khamoshi se kaam karti hai aur headlines apne aap likha leti hai."
    ],
    "movies": [
        "Box office pe numbers badhe ya na badhe, desi audience ka craze kabhi kam nahi hota.",
        "Bollywood fir se experimental mood me — par audience ab content-driven hai boss.",
        "South cinema ka impact real hai, ab Bollywood ko bhi realism seekhna hoga.",
        "Star power achha hai, par ab story hi king hai — audience ne clear message de diya hai."
    ],
    "generic": [
        "Headline mil gayi, logic gayab. Yeh news industry ka naya syllabus hai.",
        "Kahani har din nayi, par drama purana — desh ka TRP circus chalu hai.",
        "Breaking news: common sense fir se missing report hua hai.",
        "Aaj ki khabar sun ke laga satire bhi serious lagta hai ab."
    ]
}


# ------------- TOPIC MATCHER -------------
def choose_reaction(headline: str) -> str:
    lower = headline.lower()
    if any(w in lower for w in ["cricket", "bcci", "rohit", "kohli", "world cup", "odi", "t20"]):
        return random.choice(REACTIONS["cricket"])
    if "pakistan" in lower:
        return random.choice(REACTIONS["pakistan"])
    if "rahul" in lower or "gandhi" in lower:
        return random.choice(REACTIONS["rahul"])
    if "supreme court" in lower:
        return random.choice(REACTIONS["supreme"])
    if "bbc" in lower or "media" in lower or "press" in lower:
        return random.choice(REACTIONS["media"])
    if any(w in lower for w in ["movie", "film", "box office", "bollywood", "cinema", "collection"]):
        return random.choice(REACTIONS["movies"])
    return random.choice(REACTIONS["generic"])


# ------------- HASHTAGS -------------
HASHTAGS = {
    "cricket": ["#TeamIndia", "#Cricket", "#RohitSharma", "#ViratKohli"],
    "pakistan": ["#IndiaFirst", "#NationalSecurity"],
    "rahul": ["#Politics", "#Bharat"],
    "supreme": ["#Judiciary", "#IndiaNews"],
    "media": ["#FakeNarrative", "#IndianMedia"],
    "movies": ["#Bollywood", "#BoxOffice", "#IndianCinema"],
    "generic": ["#India", "#Bharat"]
}


# ------------- BUILD TWEET -------------
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
    elif "supreme court" in lower:
        key = "supreme"
    elif "media" in lower or "bbc" in lower:
        key = "media"
    elif any(w in lower for w in ["movie", "film", "box office", "bollywood", "cinema", "collection"]):
        key = "movies"

    tags = " ".join(random.sample(HASHTAGS[key], k=min(2, len(HASHTAGS[key]))))
    tweet = f"{headline} — {reaction} {tags}"
    if len(tweet) > 280:
        tweet = tweet[:277] + "..."
    return tweet


# ------------- POST TWEET (v1.1) -------------
def post_tweet():
    api = get_v1_client()
    text = build_tweet()
    print("Posting:", text)
    try:
        api.update_status(text)
        print("✅ Tweet posted (v1.1 endpoint).")
    except Exception as e:
        print("Tweet failed:", e)
        sys.exit(1)


# ------------- MAIN -------------
if __name__ == "__main__":
    post_tweet()

# tweet.py  –  ANI-based headline + aggressive reaction generator
import os, re, random, sys
import feedparser, tweepy

ANI_RSS_URL = "https://aniportalimages.blob.core.windows.net/mediafeed/news-feed.xml"

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


# --- headline fetch and cleanup ------------------------------------------------
def get_clean_headline():
    try:
        feed = feedparser.parse(ANI_RSS_URL)
        if not feed.entries:
            return "No new headline"
        raw = feed.entries[0].title
        clean = re.sub(r"http\S+|www\S+|#\S+|@\S+|ANI|–|—", "", raw).strip()
        return clean
    except Exception as e:
        print("Feed error:", e)
        return "Headline unavailable"


# --- reaction bank -------------------------------------------------------------
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
        "BCCI se zyada Twitter experts batting order decide karte hain, par runs score karta hai Rohit hi.",
        "Kohli ke cover drive ko dekhke lagta hai physics optional subject hai.",
        "Har baar jab India harata hai, critics jaag jaate hain; jab jeetta hai toh mute pe chale jaate hain.",
        "World Cup ka stress sirf fans ko nahi, bowlers ko nightmare deta hai jab Rohit set hota hai.",
        "Team India ke dressing room mein silence bhi motivation hota hai.",
        "Rohit aur Virat ke beech rivalry nahi, hunger hai — aur wahi difference bana deta hai Team India ko unique.",
        "Kuch log kehte hain age ho gayi, par performance numbers dekhke lagta hai calendar hi outdated hai.",
        "Opposition bowlers ke liye nightmare word ka synonym hai 'Kohli on song'.",
        "Cricket sirf game nahi, Bharat ke liye festival hai — aur Rohit-Virat uske brand ambassadors.",
        "Har match se pehle trolls ke predictions aate hain, match ke baad unke accounts silent ho jaate hain.",
        "Rohit ka pull shot aur Kohli ka chase — dono Bharat ke mood swings define karte hain.",
        "Team India ka aggression 'sledging' nahi, professionalism ka upgraded version hai.",
        "Fans ko sirf win nahi chahiye, domination chahiye — aur yeh squad deliver kar raha hai.",
        "Commentators keh rahe the old era khatam — bhai Rohit-Virat ne prove kar diya, form temporary hai class permanent.",
        "Jab Kohli century banata hai, trolls data delete karne lagte hain.",
        "Cricket ground pe noise kam aur impact zyada — that’s Rohit-Virat culture.",
        "Ye team khamoshi se kaam karti hai aur headlines apne aap likha leti hai."
    ],
    "generic": [
        "Headline mil gayi, logic gayab. Yeh news industry ka naya syllabus hai.",
        "Kahani har din nayi, par drama purana — desh ka TRP circus chalu hai.",
        "Breaking news: common sense fir se missing report hua hai.",
        "Aaj ki khabar sun ke laga satire bhi serious lagta hai ab."
    ]
}



# --- simple topic matcher ------------------------------------------------------
def choose_reaction(headline: str) -> str:
    lower = headline.lower()

    # --- Cricket detection first ---
    if any(w in lower for w in ["cricket", "bcci", "rohit", "kohli", "india vs", "world cup", "odi", "t20"]):
        return random.choice(REACTIONS["cricket"])

    # --- Country / politics / media topics ---
    if "pakistan" in lower:
        return random.choice(REACTIONS["pakistan"])
    if "rahul" in lower or "gandhi" in lower:
        return random.choice(REACTIONS["rahul"])
    if "supreme court" in lower or "sc " in lower:
        return random.choice(REACTIONS["supreme"])
    if "bbc" in lower or "media" in lower or "press" in lower:
        return random.choice(REACTIONS["media"])

    # --- Default fallback ---
    return random.choice(REACTIONS["generic"])



# --- build tweet ---------------------------------------------------------------
def build_tweet():
    headline = get_clean_headline()
    reaction = choose_reaction(headline)
    tweet = f"{headline} — {reaction}"
    if len(tweet) > 280:
        tweet = tweet[:277] + "..."
    return tweet


# --- post tweet ----------------------------------------------------------------
def post_tweet():
    client = get_tweepy_client()
    if not client:
        sys.exit("No Tweepy client; check keys.")
    text = build_tweet()
    print("Posting:", text)
    try:
        client.create_tweet(text=text)
        print("✅ Tweet posted successfully.")
    except Exception as e:
        print("Tweet failed:", e)
        sys.exit(1)


if __name__ == "__main__":
    post_tweet()

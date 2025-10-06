# tweet.py
import os
import random
import sys
import tweepy
import feedparser

# ------------------------
# Initialize Twitter Client
# ------------------------
def get_tweepy_client():
    try:
        client = tweepy.Client(
            consumer_key=os.getenv("X_API_KEY"),
            consumer_secret=os.getenv("X_API_SECRET"),
            access_token=os.getenv("X_ACCESS_TOKEN"),
            access_token_secret=os.getenv("X_ACCESS_SECRET")
        )
        if not (os.getenv("X_API_KEY") and os.getenv("X_API_SECRET") and os.getenv("X_ACCESS_TOKEN") and os.getenv("X_ACCESS_SECRET")):
            raise RuntimeError("Missing one or more Twitter API environment variables.")
        return client
    except Exception as e:
        print(f"CRITICAL: Failed to initialize Tweepy Client. Error: {e}")
        return None

# ------------------------
# Config
# ------------------------
NEWS_RSS_URL = os.getenv("NEWS_RSS_URL", "https://timesofindia.indiatimes.com/rssfeedstopstories.cms")

# ------------------------
# Template Bank (Alpha Bharat Mode)
# ------------------------
TEMPLATES = {
    "cricket": [
        "Bharat jab field par utarta hai, tab match nahi hota — talent aur himmat ka parade hota hai. Pakistan aur Australia samjhen ya na samjhen, dominance ka yeh naya format hai.",
        "Cricket baaki deshon ke liye sport hoga, par Bharat ke liye yeh warning system hai. Jo saamne aayega, woh ya toh seekhega ya phir silence mein ghar jayega.",
        "BBC wale keh rahe the India overhyped hai. Bhai, overhyped nahi — overpowered hai. Scoreboard pe nahi, aankhon mein dikh raha tha.",
        "Opposition ke tareeke alag hote hain — woh press conference karte hain. Hum ground par jawab dete hain.",
        "Kuch log kehte hain ‘pressure game tha’. Bhai woh pressure unke liye tha. Bharat toh aise match mein coffee peeta hai aur neeche se ground hilata hai.",
        "England aur Australia strategy banate hain. India sirf intent dikhata hai. Aur intent jab Indian ho, toh strategy dustbin mein chali jaati hai.",
        "Jo keh rahe the Bharat sirf home ground pe jeetta hai, unhe yaad dila do — warrior ko jagah nahi, bas mauka chahiye.",
        "Bharat ke bowlers ball nahi daalte — courtroom khol dete hain. Every delivery = interrogation.",
        "Kuch teams batting karte waqt nervous hoti hain. Bharat batting karte waqt background music budget decide karta hai.",
        "Pakistan ko lagta hai cricket diplomacy se relation improve hoga. Bhai pehle scoreboard pe khudka status improve karo.",
        "Bharat ki form dekh ke ICC ko rulebook revise karna padega. Yeh normal cricket nahi raha, yeh intimidation protocol hai.",
        "Australian media bol rahi thi India flat track bully hai. Bhai, bully ho ya dragon — result wahi hai: opposition roasted.",
        "Cricket ka asli maza tab aata hai jab Bharatiya players halki si smile ke saath poori team dismantle karte hain.",
        "Dusri team plan banati hai ki ball pe kaise run lena hai. Bharat plan banata hai ki ball pe unki izzat kaise leni hai.",
        "South Africa fast bowling ka garv karte the. Aaj pata chala speed aur spirit mein difference hota hai.",
        "Commentators bol rahe the ‘India under pressure’. Bhai darr toh unki awaaz mein tha, players mein nahi.",
        "Bharat jab toss jeetta hai, opposition ke WhatsApp groups mein silence ho jata hai.",
        "Cricket ka level tab samajh aata hai jab doosri team coin toss ke waqt hi pray karna shuru kar deti hai.",
        "Woh shot sirf boundary nahi tha — ek reminder tha ki Bharat sirf khelega nahi, command bhi karega.",
        "Jo India ko underestimate karte hain, unka match khatam hone ke baad Google search history sab bata deti hai: ‘How to recover from humiliation’"
    ],
    "geopolitics": [
        "BBC phir se lecture de raha hai Indian democracy par. Bhai, pehle apna Prime Minister stable rakh lo — humari advice baad mein lena.",
        "Western media ka pattern simple hai — jab Bharat apna kaam kare, toh usse ‘aggressive’ bolo. Jab woh baith ke sunta rahe, tab ‘silent spectator’ bolo. Bhai hum tumhare report card ke liye nahi jeete.",
        "Pakistan UN mein speech deta hai. Bharat reply nahi deta — Bharat border par calculation deta hai.",
        "China samjhta hai ki dominance ke liye volume chahiye. Bhai, hum ek line bolte hain — aur woh line unke saare calculation tod deti hai.",
        "Europe wale climate change lecture de rahe hain. Bhai pedal chal ke colony mein dustbin toh pahunch jao pehle, phir world ko gyaan dena.",
        "Kuch log kehte hain Bharat ko negotiation seekhna chahiye. Bhai negotiation nahi — declaration samjhte ho?",
        "Biden bol rahe the allies important hain. Bharat bol raha hai self-respect sabse important hai.",
        "Foreign think-tanks ke liye India ek ‘rising power’ hogi. Par ground reality yeh hai — yeh power sirf rise nahi kar raha, reshape kar raha hai.",
        "Jab Bharat aid deta hai toh ‘moral responsibility’. Jab Bharat arms kharidne se mana kare toh ‘strategic aggression’. Kitna dimaag maaroge bhai?",
        "Kuch log bol rahe the ‘Bharat ko flexible hona chahiye’. Bhai flexibility yoga mein hoti hai, foreign policy mein nahi.",
        "Pakistan ko lagta hai press conference se narrative change hota hai. Bharat ko pata hai silence se battlefield change hota hai.",
        "Foreign media ke liye Bharat ka sabse bada crime hai — ki yeh ab permission nahi poochta.",
        "IMF ke loans aur Bharat ke decisions mein ek difference hota hai — unka interest hota hai, humara intent.",
        "UN resolution ek paper hota hai. Indian retaliation ek paragraph hota hai jisme signature nahi, footprint hota hai.",
        "Jinhone India ko ‘third world’ bola tha, ab woh khud third priority ban chuke hain humare schedule mein.",
        "China road banata hai, Bharat relationship banata hai. Aur jab Bharat road banata hai — woh seedha unki ego pe jata hai.",
        "Kuch log kehte hain India aur Pakistan table pe baith ke baat karen. Bhai table toot jayegi, pehle ground pe jawab toh handle karo.",
        "America ke sanctions aur India ke silence mein difference hai — ek pressure create karta hai, doosra history.",
        "Foreign policy ab diplomacy nahi, demonstration ban chuki hai.",
        "Jo desh humse ‘tone down’ bol rahe the kal, aaj woh khud humse tone le rahe hain."
    ],
        "news": [
        "Opposition ka pura agenda ek hi line mein fit hota hai — ‘Kaam zero, shor hundred’.",
        "Kuch log bolte hain inflation high hai. Bhai unka inflation sirf mic ke bill ka hai, sach mein kya ho raha hai woh unhe kab samajh aayega?",
        "Liberals ka logic simple hai — agar Bharat jeete toh problem, agar na jeete toh aur problem.",
        "Media wale headline banate hain ‘India divided’. Bhai divided toh TRP channel hai, public nahi.",
        "Leftists ko har cheez mein ‘attack on democracy’ dikhai deta hai. Electricity cut ho jaye toh bhi dictatorship bol denge.",
        "Kuch neta sirf election ke waqt Hindu-Muslim karte hain. Bharat ka asli voter ab data dekhta hai, drama nahi.",
        "Ye woh log hain jo foreign trips mein Bharat ki burai karte hain aur phir airport lounge mein selfie lete hain.",
        "Pehle ke leaders speech dete the, aaj ke leaders result dete hain. Aur wahi unhe hazam nahi ho raha.",
        "Fake activists baar baar arrest hone ka drama karte hain. Bhai jail nahi stage nahi hai.",
        "Unhe freedom of speech tab yaad aata hai jab unka mic bandh ho, jab desh ka kaam roke tab unhe silence suit karta hai.",
        "Media ka kaam pehle news dena tha, ab narrative banana ho chuka hai. Par Bharat ka public ab remote control nahi hai.",
        "Kuch log kehte hain padhai pe dhyaan do. Bhai, issi padhai ne bata diya ki kaun sach bol raha hai aur kaun devoted hai sirf TRP ke liye.",
        "Pehle ke politicians ke paas files hoti thi. Aaj ke politicians ke paas footage hota hai.",
        "Jo log keh rahe hain India intolerant hai, woh khud intolerant hai India ke progress se.",
        "Sabko equality chahiye, par jab Bharat world stage pe equal treatment maange toh sabko mirchi lagti hai.",
        "Opposition rally karte hain, Bharat rally nahi karta — Bharat verdict deta hai.",
        "TRP ke liye journalism theek hai, par national interest ke khilaaf scripting nahi chalega.",
        "Yeh woh log hain jo har baat mein constitution quote karte hain, par khud kabhi preamble padha bhi nahi hoga.",
        "Political drama ka asli analysis sirf ek line mein — kaam karo ya side ho jao.",
        "Kuch logon ko desh tab yaad aata hai jab unhe footage chahiye hota hai. Bharat ko aise freeloaders ki zaroorat nahi hai."
    ]
}

# ------------------------
# Helpers
# ------------------------
def get_latest_headline(rss_url):
    try:
        feed = feedparser.parse(rss_url)
        if feed.entries and len(feed.entries) > 0:
            return feed.entries[0].title
        return "Desh aur duniya ki khabar"
    except:
        return "Desh aur duniya ki khabar"

def build_message():
        topic = random.choice(["cricket", "geopolitics", "news"])
        if topic == "news":
            headline = get_latest_headline(NEWS_RSS_URL)
            template = random.choice(TEMPLATES["news"])
            msg = f"{template} — {headline}"
        else:
            msg = random.choice(TEMPLATES[topic])
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
        raise RuntimeError(f"Error during tweet creation: {e}")

# ------------------------
# Entrypoint
# ------------------------
if __name__ == "__main__":
    try:
        post_random_tweet()
    except Exception as exc:
        print(f"[ERROR] {exc}")
        sys.exit(1)
    sys.exit(0)


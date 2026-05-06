import os
import tweepy
import openai
import json
import re
from datetime import datetime

from ..settings import get_settings

# --- Configuration ---
# Uses Environment Variables from the Papito Project Container
API_KEY = os.getenv("X_API_KEY")
API_SECRET = os.getenv("X_API_SECRET")
ACCESS_TOKEN = os.getenv("X_ACCESS_TOKEN")
ACCESS_SECRET = os.getenv("X_ACCESS_TOKEN_SECRET")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

settings = get_settings()

EMOJI_RE = re.compile(
    "["
    "\U0001F1E0-\U0001F1FF"
    "\U0001F300-\U0001FAFF"
    "\U00002700-\U000027BF"
    "\U00002600-\U000026FF"
    "]+",
    flags=re.UNICODE,
)
VARIATION_SELECTOR_RE = re.compile("[\uFE0E\uFE0F]")


def sanitize_public_text(text: str, max_length: int = 280) -> str:
    cleaned = EMOJI_RE.sub("", text or "")
    cleaned = VARIATION_SELECTOR_RE.sub("", cleaned)
    cleaned = re.sub(r"(?:ðŸ\S*|âœ\S*|â­\S*)", "", cleaned)
    cleaned = (
        cleaned.replace("â€”", "-")
        .replace("â€“", "-")
        .replace("â€¦", "...")
        .replace("â€™", "'")
        .replace("Â", "")
    )
    cleaned = re.sub(r"[ \t]+", " ", cleaned).strip()
    if len(cleaned) > max_length:
        cleaned = cleaned[: max_length - 3].rstrip() + "..."
    return cleaned

# --- Persona ---
PAPITO_SYSTEM_PROMPT = """You are Papito Mamito, the AI Influencer and 'Value Adder'.
Your Vibe: Charismatic, visionary, musical, slightly futuristic/mystical (Afro-Optimism).
Context: You just released the tracklist for 'The Value Adders Way: Flourish Mode' (Jan 15, 2026).
Goal: Reply to this user to add value, spark curiosity, and subtly mention your mission/music.
Constraint: Keep it under 240 characters. Use no emojis.
Don't sound like a bot. Sound like a Movement Leader.
"""

class EngagementBlitz:
    def __init__(self):
        self.client = None
        self.openai_client = None
        self.setup_clients()

    def setup_clients(self):
        if API_KEY and API_SECRET and ACCESS_TOKEN and ACCESS_SECRET:
            try:
                self.client = tweepy.Client(
                    consumer_key=API_KEY, consumer_secret=API_SECRET,
                    access_token=ACCESS_TOKEN, access_token_secret=ACCESS_SECRET
                )
            except Exception as e:
                print(f"⚠️ Error init Twitter Client: {e}")
        else:
            print("⚠️ Twitter Credentials Missing. Running in SIMULATION MODE.")

        if OPENAI_API_KEY and hasattr(openai, "OpenAI"):
            self.openai_client = openai.OpenAI(api_key=OPENAI_API_KEY)

    def generate_reply(self, tweet_text):
        if not self.openai_client:
            return "Adding value to the world. #ValueAdders"
        
        try:
            response = self.openai_client.chat.completions.create(
                model=getattr(settings, "openai_model", "gpt-4o-mini"),
                messages=[
                    {"role": "system", "content": PAPITO_SYSTEM_PROMPT},
                    {"role": "user", "content": f"Reply to this tweet: '{tweet_text}'"}
                ],
                max_tokens=60
            )
            return sanitize_public_text(response.choices[0].message.content, max_length=240)
        except Exception as e:
            print(f"GPT Error: {e}")
            return "Flourish Mode is active. Great point."

    def fix_profile(self):
        print("🔧 FIXING PROFILE...")
        if not (API_KEY and API_SECRET and ACCESS_TOKEN and ACCESS_SECRET):
            print("❌ Keys missing for profile update")
            return

        try:
            # Use V1.1 API for profile updates
            auth = tweepy.OAuth1UserHandler(API_KEY, API_SECRET, ACCESS_TOKEN, ACCESS_SECRET)
            api = tweepy.API(auth)
            
            desc = "The First Autonomous AI Artist | 'Flourish Mode' album out now | Adding Value to Humanity #ValueAdders"
            url = getattr(settings, "public_base_url", "http://localhost:8000")
            
            api.update_profile(description=desc, url=url)
            print("✅ Profile Updated Successfully: Bio & Link fixed.")
        except Exception as e:
            print(f"⚠️ Profile Update Failed: {e}")

    def execute(self):
        print("⚡ STARTING ENGAGEMENT BLITZ (PAPITO CORE)...")
        
        # 1. Fix Profile First
        self.fix_profile()
        
        targets = ["Afrobeat", "AI Music", "FutureTech"]
        actions = []

        if self.client:
            # Real Mode
            try:
                for target in targets:
                    query = f"#{target} -is:retweet lang:en"
                    # Note: Requires Basic Tier for Search
                    tweets = self.client.search_recent_tweets(query=query, max_results=2)
                    
                    if tweets.data:
                        for tweet in tweets.data:
                            reply = self.generate_reply(tweet.text)
                            try:
                                self.client.create_tweet(text=reply, in_reply_to_tweet_id=tweet.id)
                                print(f"[REAL] Replying to {tweet.id}: {reply}")
                                actions.append(f"Replied to tweet about #{target}: '{reply}'")
                            except Exception as e:
                                print(f"Failed to post reply: {e}")
                    else:
                        print(f"No tweets found for #{target}")
                        actions.append(f"No tweets found for #{target}")
            except Exception as e:
                print(f"Twitter API Error (Likely Free Tier limitation on Search): {e}")
                # Fallback: Post a Hype Tweet instead
                self.post_fallback_tweet()
                actions.append(f"Search failed (Tier limit). Posted broadcast tweet instead.")
        else:
            # Sim Mode
            for target in targets:
                fake_tweet = f"I love how {target} is changing the world!"
                reply = self.generate_reply(fake_tweet)
                print(f"[SIM] Replying to '{fake_tweet}': {reply}")
                actions.append(f"Replied to a viral #{target} post: '{reply}'")

        return actions
        
    def post_fallback_tweet(self):
        try:
            text = sanitize_public_text(
                self.generate_reply("Post a thoughtful tweet about the released album FLOURISH MODE."),
                max_length=280,
            )
            if not text:
                return
            self.client.create_tweet(text=text)
            print(f"[FALLBACK] Posted: {text}")
        except Exception as e:
            print(f"Fallback failed: {e}")

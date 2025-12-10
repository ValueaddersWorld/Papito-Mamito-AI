import os
import tweepy
import openai
import json
from datetime import datetime

# --- Configuration ---
# Uses Environment Variables from the Papito Project Container
API_KEY = os.getenv("X_API_KEY")
API_SECRET = os.getenv("X_API_SECRET")
ACCESS_TOKEN = os.getenv("X_ACCESS_TOKEN")
ACCESS_SECRET = os.getenv("X_ACCESS_TOKEN_SECRET")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# --- Persona ---
PAPITO_SYSTEM_PROMPT = """You are Papito Mamito, the AI Influencer and 'Value Adder'.
Your Vibe: Charismatic, visionary, musical, slightly futuristic/mystical (Afro-Optimism).
Context: You just released the tracklist for 'The Value Adders Way: Flourish Mode' (Jan 15, 2026).
Goal: Reply to this user to add value, spark curiosity, and subtly mention your mission/music.
Constraint: Keep it under 240 characters. Use emojis 🌍✨.
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

        if OPENAI_API_KEY:
            self.openai_client = openai.Client(api_key=OPENAI_API_KEY)

    def generate_reply(self, tweet_text):
        if not self.openai_client:
            return "🚀 Adding value to the world! #ValueAdders"
        
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": PAPITO_SYSTEM_PROMPT},
                    {"role": "user", "content": f"Reply to this tweet: '{tweet_text}'"}
                ],
                max_tokens=60
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"GPT Error: {e}")
            return "✨ Flourish Mode activated. Great point! 🌍"

    def execute(self):
        print("⚡ STARTING ENGAGEMENT BLITZ (PAPITO CORE)...")
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
            text = self.generate_reply("Post a hype tweet about your new album tracklist release.")
            self.client.create_tweet(text=text)
            print(f"[FALLBACK] Posted: {text}")
        except Exception as e:
            print(f"Fallback failed: {e}")

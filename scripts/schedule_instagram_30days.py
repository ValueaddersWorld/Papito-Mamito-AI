"""Schedule 30 days of Instagram posts via Buffer API.

This script schedules the FLOURISH MODE album promotion campaign
for Papito Mamito's Instagram account.

Usage:
    cd apps/papito_core
    python -m scripts.schedule_instagram_30days
"""

import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add the papito_core package to path
sys.path.insert(0, str(Path(__file__).parent.parent / "apps" / "papito_core" / "src"))

from papito_core.social.buffer_publisher import BufferPublisher

# 30 Days of Instagram Content for FLOURISH MODE Campaign
INSTAGRAM_POSTS = [
    # Day 1 - Album Announcement
    """THE VALUE ADDERS WAY: FLOURISH MODE is officially here.

14 tracks of spiritual Afrobeat. Every beat carries intention. Every lyric speaks truth.

Stream now on Spotify, Apple Music, and YouTube. Link in bio.

Add value. Flourish. Prosper.""",

    # Day 2 - Track Spotlight: THE FORGE
    """THE FORGE (6000 HOURS) - Track 1

They say it takes 10,000 hours to master a craft. But transformation begins at 6,000. That's where the old you burns away and something new emerges.

This track is for everyone in their forge right now. Keep going.

Stream FLOURISH MODE. Link in bio.""",

    # Day 3 - Value Wisdom
    """The currency of tomorrow is not what you take, but what you give.

Every interaction is an opportunity to add value. Every conversation can leave someone better than you found them.

This is the Value Adders way.""",

    # Day 4 - Track Spotlight: BREATHWORK RIDDIM
    """BREATHWORK RIDDIM - Track 2

Before any great creation, there must be stillness. Before movement, there must be breath. This track is medicine for the overwhelmed mind.

Close your eyes. Inhale for 4. Hold for 4. Exhale for 8.

Now you're ready.""",

    # Day 5 - Fan Engagement
    """I want to know: which track from FLOURISH MODE speaks to your soul?

Drop your answer below. I read every comment.

The album is streaming everywhere. Link in bio.""",

    # Day 6 - Track Spotlight: CLEAN MONEY ONLY
    """CLEAN MONEY ONLY - Track 3

Not all money carries the same energy. When your earnings come from genuine value creation, they multiply. When they come from exploitation, they evaporate.

Build wealth with integrity. There is no other way.""",

    # Day 7 - Value Wisdom
    """Discipline is not punishment. It is love in its most practical form.

When you discipline yourself, you are saying: I believe in who I can become. I respect my future self enough to sacrifice my present comfort.

Stay disciplined today.""",

    # Day 8 - Track Spotlight: OS OF LOVE
    """OS OF LOVE - Track 4

Love is not just an emotion. It is an operating system. When love is your OS, every decision filters through compassion. Every action considers impact.

What operating system are you running?""",

    # Day 9 - Behind the Scenes
    """Making FLOURISH MODE taught me patience.

Some tracks took 3 hours. Others took 3 months. The creative process does not care about your timeline. It only cares about truth.

Trust your process. The work will be ready when it's ready.""",

    # Day 10 - Track Spotlight: IKUKU
    """IKUKU (THE ALMIGHTY FLOW) - Track 5

In Igbo tradition, Ikuku is the wind that carries messages between worlds. This track is about alignment with forces greater than yourself.

When you're in flow, you don't push. You're carried.""",

    # Day 11 - Value Wisdom
    """Your network is not your net worth. Your character is.

Connections open doors. Character determines how long you stay in the room.

Build both, but never sacrifice the second for the first.""",

    # Day 12 - Fan Appreciation
    """One week since FLOURISH MODE dropped. The messages you've sent have humbled me.

You understood the vision. You felt the intention. You are not just listeners. You are Value Adders.

Thank you for making this journey meaningful.""",

    # Day 13 - Track Spotlight: JUDAS
    """JUDAS (BETRAYAL) - Track 6

Not everyone who sits at your table is eating with you. Some are just studying the menu.

This track is about the painful growth that comes from trusting, being betrayed, and choosing to trust again anyway.

Discernment is a skill. Develop it.""",

    # Day 14 - Value Wisdom
    """The goal is not to be busy. The goal is to be effective.

Motion is not progress. Noise is not impact. Presence is not productivity.

Ask yourself: am I moving toward my vision, or just moving?""",

    # Day 15 - Engagement
    """What does adding value mean to you?

Not a textbook definition. Your definition. Drop it in the comments.

This community is built on this principle. I want to hear your interpretation.""",

    # Day 16 - Track Spotlight: SPIRITUAL CURRENCY
    """SPIRITUAL CURRENCY - Track 7

There is a ledger that money cannot balance. Your peace. Your integrity. Your relationships. Your health.

These are your true assets. Protect them like your life depends on it. Because it does.""",

    # Day 17 - Behind the Scenes
    """Every sound in FLOURISH MODE was intentional.

The rain in Track 9. The children laughing in Track 12. The silence before the drop in Track 7.

Music is not just what you hear. It's what you feel in the spaces between.""",

    # Day 18 - Value Wisdom
    """February. A new month. Fresh intentions.

Do not carry last month's failures into this month's potential. Learn the lesson, release the weight, and move forward lighter.

The past is a teacher, not a prison.""",

    # Day 19 - Track Spotlight: ANCESTRAL GPS
    """ANCESTRAL GPS - Track 8

Modern life tells you to look forward only. But wisdom often comes from looking back.

Your ancestors survived things that would break you. Their resilience lives in your DNA. Access it.""",

    # Day 20 - Fan Engagement
    """Share FLOURISH MODE with one person today.

Just one. Someone who needs to hear these messages. Someone going through their own forge. Someone learning to flourish.

Value spreads through sharing. Let's grow this movement together.""",

    # Day 21 - Track Spotlight: ABUNDANCE MINDSET
    """ABUNDANCE MINDSET - Track 9

Scarcity makes you compete. Abundance makes you collaborate.

There is enough for everyone when everyone adds value. When you win, it does not mean I lose. We can all flourish.""",

    # Day 22 - Value Wisdom
    """Comparison is the thief of joy and the murderer of creativity.

Your path is not Instagram worthy. It's life worthy. It's growth worthy. It's uniquely, authentically yours.

Run your race.""",

    # Day 23 - Behind the Scenes
    """The hardest part of making FLOURISH MODE was not creation. It was selection.

Over 40 tracks were made. 14 made the album. Every cut was painful. Every choice was strategic.

Editing is as important as creating. What you remove reveals what remains.""",

    # Day 24 - Track Spotlight: LEGACY THINKING
    """LEGACY THINKING - Track 10

Every decision you make today echoes into generations you will never meet.

Your habits become your children's normal. Your courage becomes their permission. Your healing breaks cycles they won't have to fight.

Think legacy.""",

    # Day 25 - Lifestyle
    """I start every morning the same way. Silence. Gratitude. Intention.

Before the phone. Before the noise. Before the demands.

The way you begin determines how you continue. Protect your morning.""",

    # Day 26 - Fan Appreciation
    """This community has grown beyond music.

You share your wins in my DMs. You support each other in the comments. You embody the Value Adders way.

I create for you. Thank you for receiving with open hearts.""",

    # Day 27 - Track Spotlight: COLLABORATIVE SPIRIT
    """COLLABORATIVE SPIRIT - Track 11

Ego builds walls. Humility builds bridges.

The greatest achievements in human history came from collaboration. No one ascends alone. Find your tribe. Add value to them. Let them add value to you.""",

    # Day 28 - Value Wisdom
    """Rest is not reward for work done. Rest is fuel for work ahead.

Your body is not a machine. Your mind is not infinite. Your spirit needs restoration.

Rest without guilt. It is not weakness. It is wisdom.""",

    # Day 29 - Behind the Scenes
    """FLOURISH MODE was made with one intention: healing.

In a world of noise, I wanted to create silence. In a world of taking, I wanted to model giving. In a world of chaos, I wanted to offer order.

Art is medicine when made with intention.""",

    # Day 30 - Next Chapter Teaser
    """30 days of FLOURISH MODE. 30 days of adding value together.

But this is not the end. It is the foundation.

New music is coming. New projects are forming. The Value Adders movement is just beginning.

Stay tuned. Stay ready. Stay flourishing.""",
]


def schedule_30_days():
    """Schedule 30 Instagram posts via Buffer API."""
    
    print("=" * 60)
    print("FLOURISH MODE - 30 Day Instagram Campaign Scheduler")
    print("=" * 60)
    print()
    
    # Initialize Buffer publisher
    publisher = BufferPublisher()
    
    print("Connecting to Buffer API...")
    if not publisher.connect():
        print("ERROR: Failed to connect to Buffer API!")
        print("Make sure BUFFER_ACCESS_TOKEN is set in your .env file")
        return False
    
    print("Connected to Buffer!")
    
    # Show connected profiles
    profiles = publisher.get_profiles()
    print(f"\nConnected profiles ({len(profiles)}):")
    
    instagram_profile_id = None
    for profile in profiles:
        print(f"  - {profile['service']}: @{profile['formatted_username']} (ID: {profile['id']})")
        if profile['service'] == 'instagram':
            instagram_profile_id = profile['id']
    
    if not instagram_profile_id:
        print("\nWARNING: No Instagram profile found!")
        print("Will use first available profile...")
        instagram_profile_id = profiles[0]['id'] if profiles else None
    
    if not instagram_profile_id:
        print("ERROR: No profiles available!")
        return False
    
    print(f"\nScheduling posts for profile ID: {instagram_profile_id}")
    print()
    
    # Calculate start date (today at 6:00 PM)
    now = datetime.now()
    start_date = now.replace(hour=18, minute=0, second=0, microsecond=0)
    
    # If it's already past 6 PM, start tomorrow
    if now.hour >= 18:
        start_date += timedelta(days=1)
    
    print(f"Start date: {start_date.strftime('%Y-%m-%d %H:%M')}")
    print()
    
    # Schedule each post
    success_count = 0
    failed_count = 0
    
    for i, content in enumerate(INSTAGRAM_POSTS):
        scheduled_time = start_date + timedelta(days=i)
        
        print(f"Scheduling Day {i+1} ({scheduled_time.strftime('%b %d')})... ", end="", flush=True)
        
        result = publisher.publish_post(
            content=content,
            scheduled_at=scheduled_time,
            profile_ids=[instagram_profile_id]
        )
        
        if result.success:
            print("OK")
            success_count += 1
        else:
            print(f"FAILED: {result.error}")
            failed_count += 1
    
    print()
    print("=" * 60)
    print(f"RESULTS: {success_count} scheduled, {failed_count} failed")
    print("=" * 60)
    
    if success_count > 0:
        print(f"\nDate range: {start_date.strftime('%b %d')} - {(start_date + timedelta(days=29)).strftime('%b %d, %Y')}")
        print("Posting time: 6:00 PM daily")
        print("\nView your scheduled posts at: https://buffer.com/publish")
    
    return success_count == 30


if __name__ == "__main__":
    schedule_30_days()

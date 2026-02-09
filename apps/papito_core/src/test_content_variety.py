"""Quick test to demonstrate improved content variety."""
import sys
sys.path.insert(0, '.')

from papito_core.engines.ai_personality import AIPersonalityEngine
from papito_core.automation.content_scheduler import ContentType

engine = AIPersonalityEngine()

print("=" * 60)
print("SAMPLE CONTENT FROM IMPROVED TEMPLATES")
print("=" * 60)

content_types = [
    'morning_blessing',
    'music_wisdom',
    'provocative_thought', 
    'hot_take',
    'community_question',
    'studio_diary',
    'culture_spotlight',
    'ai_reflection'
]

for ct in content_types:
    post = engine.generate_content_post(ct, 'x')
    print(f"\n[{ct.upper()}]")
    print(f"{post['text']}")
    print(f"Tags: {' '.join(post['hashtags'])}")

print("\n" + "=" * 60)
print("Total content types with 10+ variations each:")
print(f"  - Original types: morning_blessing, music_wisdom, track_snippet, behind_the_scenes, fan_appreciation")
print(f"  - NEW types: provocative_thought, community_question, hot_take, studio_diary, culture_spotlight, ai_reflection, trending_topic")
print("=" * 60)

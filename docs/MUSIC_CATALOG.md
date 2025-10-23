# Music Catalog Canon

> This catalog honours the Value Adders World storyline that Papito Mamito released his debut album **_We Rise! Wealth Beyond Money_** on 5 October 2024. Streaming availability spans Spotify, Apple Music, Deezer, iHeartRadio, iTunes, and YouTube (per canonical sources).

## Albums

### We Rise! Wealth Beyond Money (2024)
- **Release date:** 2024-10-05
- **Tracks:** 16
- **Themes:** gratitude, abundance mindset, wisdom, unity, spiritual wealth
- **Suggested singles:** "We Rise!", "Bless Me with Sense", "Wealth Beyond Money", "Chi M (My Destiny Will Be Fulfilled)"

#### Distribution Checklist
- ISRC generation (automated via distributor API)
- Metadata packaging (`papito_core.releases.metadata`)
- Artwork verification (4K master, 1:1 and 16:9 crops)
- Streaming platform delivery confirmation
- Social rollout (Instagram carousel, X digest, Value Adders newsletter)

## Release Metadata Schema
```yaml
title: string
release_date: date
type: album | single | ep
tracks:
  - title: string
    duration: mm:ss
    bpm: int
    key: string
    mood_tags: [string]
    theme_tags: [string]
    collaborators: [string]
links:
  spotify: url
  apple_music: url
  deezer: url
  youtube: url
  others: dict
promotion:
  hero_story: markdown
  call_to_action: markdown
  gratitude_rollcall: [string]
```

This schema underpins the automated release trackers and promo scripting modules in `papito_core`.

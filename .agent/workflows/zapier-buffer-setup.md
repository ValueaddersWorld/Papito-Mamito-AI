---
description: Complete guide to set up Zapier automation for Papito's autonomous content posting
---

# Zapier Automation Setup for Papito Mamito AI

Set up 3 daily automated posts optimized for Twitter's 100 posts/month budget.

## 🎯 Overview

```
Schedule (3x Daily) → Papito API → Generate Content → Post to Twitter
```

**Monthly Budget**: ~100 tweets/month
**Daily Posts**: 3 posts × 30 days = 90 posts (leaving buffer for manual posts)

---

## ✅ Prerequisites

- [ ] Zapier account (free tier: 100 tasks/month matches perfectly)
- [ ] Papito API deployed: `https://web-production-14aea.up.railway.app`
- [ ] Twitter/X API access configured in Railway environment variables

---

## 📋 The 3-Post Daily Schedule

| Time (WAT) | Content Type | Purpose |
|------------|--------------|---------|
| **7:00 AM** | `morning_blessing` | Start the day with wisdom |
| **1:00 PM** | `music_wisdom` | Midday engagement |
| **7:00 PM** | `fan_appreciation` | Evening connection |

---

## 📋 Step 1: Create Zap #1 - Morning Wisdom (7:00 AM)

### Trigger: Schedule by Zapier
1. Go to [https://zapier.com](https://zapier.com) → Create Zap
2. Name: "Papito Morning Post"
3. Search: `Schedule by Zapier`
4. Event: `Every Day`
5. Time: `7:00 AM`
6. Timezone: `Africa/Lagos (WAT)`

### Action: Webhooks by Zapier
1. App: `Webhooks by Zapier`
2. Event: `POST`
3. URL: `https://web-production-14aea.up.railway.app/webhooks/zapier/generate-post`
4. Payload Type: `json`
5. Data:
   - `content_type`: `morning_blessing`
   - `include_album`: `true`
   - `platform`: `twitter`

### Action 2: Twitter (Post Tweet)
1. App: `Twitter`
2. Event: `Create Tweet`
3. Text: Use data from Webhook:
   ```
   {{2. POST - text}}

   {{2. POST - hashtags}}
   ```

---

## 📋 Step 2: Create Zap #2 - Midday Music (1:00 PM)

Same setup as above, but:
- **Name**: "Papito Midday Post"
- **Time**: `1:00 PM`
- **content_type**: `music_wisdom`

---

## 📋 Step 3: Create Zap #3 - Evening Appreciation (7:00 PM)

Same setup as above, but:
- **Name**: "Papito Evening Post"
- **Time**: `7:00 PM`
- **content_type**: `fan_appreciation`

---

## 🔧 API Endpoints Reference

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/webhooks/zapier/generate-post` | POST | Generate refined content |
| `/webhooks/zapier/content-types` | GET | List available types |
| `/webhooks/zapier/album-status` | GET | Album countdown info |
| `/twitter/post` | POST | Direct post to Twitter |

---

## 📊 Content Types Available

| Type | Description |
|------|-------------|
| `morning_blessing` | Wisdom and intentions for the day |
| `music_wisdom` | Insights about music, creativity, AI artistry |
| `fan_appreciation` | Genuine gratitude for the community |
| `album_promo` | FLOURISH MODE countdown |
| `track_snippet` | Studio updates, 50/50 music creation |
| `challenge_promo` | #FlightMode6000 meditation challenge |

---

## ✨ Content Style Guide

Papito's refined voice:
- **Minimal emojis**: Zero to two maximum per post
- **1-2 hashtags only**: Quality over quantity
- **50/50 Music Creation**: "My music is 50% human, 50% AI. The lyrics come from human inspiration. AI creates the rest of the art."
- **Intellectual yet accessible**: Wisdom with depth
- **No hashtag spam, no emoji overload**

---

## 🔄 Test Commands

```powershell
# Test content generation
$body = @{
    content_type = "morning_blessing"
    include_album = $true
    platform = "twitter"
} | ConvertTo-Json

Invoke-RestMethod -Uri "https://web-production-14aea.up.railway.app/webhooks/zapier/generate-post" -Method Post -Body $body -ContentType "application/json"

# Direct post to Twitter
$body = @{
    generate_new = $true
    content_type = "morning_blessing"
} | ConvertTo-Json

Invoke-RestMethod -Uri "https://web-production-14aea.up.railway.app/twitter/post" -Method Post -Body $body -ContentType "application/json"
```

---

## 📈 Monthly Optimization

With 100 posts/month budget:
- **90 automated posts** (3/day × 30 days)
- **10 manual posts** for special moments, engagement, responses

---

**Add Value. We Flourish & Prosper.**

*THE VALUE ADDERS WAY: FLOURISH MODE - January 2026*

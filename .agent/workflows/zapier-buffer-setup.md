---
description: Complete guide to set up Zapier automation for Papito's autonomous content posting
---

# Zapier + Buffer Automation Setup for Papito Mamito AI

This workflow creates a fully automated content posting pipeline using Zapier to connect Papito's API to Buffer/Instagram.

## 🎯 Overview

```
Schedule (Daily) → Papito API → Generate Content → Buffer → Instagram
```

---

## ✅ Prerequisites

Before starting, ensure you have:
- [ ] Zapier account (free tier works for 1 Zap)
- [ ] Buffer account connected to Instagram
- [ ] Papito API deployed on Railway: `https://web-production-14aea.up.railway.app`

---

## 📋 Step 1: Create a New Zap

1. Go to [https://zapier.com](https://zapier.com)
2. Click **Create** → **Zaps** → **Create Zap**
3. Name your Zap: "Papito Daily Content Post"

---

## 📋 Step 2: Configure the Trigger (Schedule)

1. **Search for app**: `Schedule by Zapier`
2. **Event**: Select `Every Day`
3. **Configure Schedule**:
   - **Time of Day**: `07:00 AM` (or your preferred time)
   - **Time Zone**: `Africa/Lagos (WAT)` (optimal for Afrobeat audience)
   - **Days of the Week**: Select all 7 days
4. Click **Continue**
5. Click **Test trigger** to verify

---

## 📋 Step 3: Add Webhook Action (Call Papito API)

1. Click the **+** button to add an action
2. **Search for app**: `Webhooks by Zapier`
3. **Event**: Select `POST`
4. Click **Continue**
5. **Configure the webhook**:

   | Field | Value |
   |-------|-------|
   | **URL** | `https://web-production-14aea.up.railway.app/webhooks/zapier/generate-post` |
   | **Payload Type** | `json` |
   | **Data** | See below |

   **Data fields** (add each as a separate row):
   
   | Key | Value |
   |-----|-------|
   | `content_type` | `morning_blessing` |
   | `include_album` | `true` |
   | `platform` | `instagram` |

6. Click **Continue**
7. Click **Test action** - You should get a response like:
   ```json
   {
     "success": true,
     "text": "🌅 Rise with purpose...",
     "hashtags": "#PapitoMamito #FlourishMode...",
     "content_type": "morning_blessing",
     "platform": "instagram",
     "album_countdown": 39
   }
   ```

---

## 📋 Step 4: Add Buffer Action (Post to Instagram)

1. Click the **+** button to add another action
2. **Search for app**: `Buffer`
3. **Event**: Select `Add to Queue`
4. Click **Continue**
5. **Connect Buffer account** if not already connected
6. **Configure Buffer**:

   | Field | Value |
   |-------|-------|
   | **Profile** | Select your Instagram profile |
   | **Text** | Use the **Insert Data** button to select: |
   | | `2. POST in Webhooks → Text` |
   | | Then add a line break and insert: |
   | | `2. POST in Webhooks → Hashtags` |
   | **Media** | (Optional) Leave blank or add album art URL |
   | **Schedule** | `Add to End of Queue` or `Share Now` |

   **Example combined text:**
   ```
   {{2. POST - Text}}

   {{2. POST - Hashtags}}
   ```

7. Click **Continue**
8. Click **Test action** to verify the post appears in Buffer

---

## 📋 Step 5: Turn On Your Zap

1. Click **Publish** in the top-right corner
2. Your Zap is now live and will run daily!

---

## 🎨 Content Type Variations

Create multiple Zaps with different content types for variety:

| Content Type | Description | Best Time |
|-------------|-------------|-----------|
| `morning_blessing` | Uplifting morning motivation | 7:00 AM |
| `music_wisdom` | Insights about music & creativity | 12:00 PM |
| `challenge_promo` | #FlightMode6000 challenge promotion | 3:00 PM |
| `album_promo` | Album announcement/hype | 6:00 PM |
| `fan_appreciation` | Thank you to supporters | 9:00 PM |
| `flourish_index` | Flourish Index inspiration | Weekends |

---

## 🔄 Advanced: Multiple Daily Posts

Create 3 separate Zaps for different times:

### Zap 1: Morning Motivation (7:00 AM)
```json
{
  "content_type": "morning_blessing",
  "include_album": true,
  "platform": "instagram"
}
```

### Zap 2: Midday Wisdom (1:00 PM)
```json
{
  "content_type": "music_wisdom",
  "include_album": false,
  "platform": "instagram"
}
```

### Zap 3: Evening Album Promo (7:00 PM)
```json
{
  "content_type": "album_promo",
  "include_album": true,
  "platform": "instagram"
}
```

---

## 🔧 API Endpoints Reference

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/webhooks/zapier/generate-post` | POST | Generate content |
| `/webhooks/zapier/content-types` | GET | List available types |
| `/webhooks/zapier/album-status` | GET | Album countdown info |

### Test endpoints manually:

```powershell
# Get content types
Invoke-RestMethod -Uri "https://web-production-14aea.up.railway.app/webhooks/zapier/content-types"

# Get album status
Invoke-RestMethod -Uri "https://web-production-14aea.up.railway.app/webhooks/zapier/album-status"

# Generate a post
$body = @{content_type = "morning_blessing"; include_album = $true; platform = "instagram"} | ConvertTo-Json
Invoke-RestMethod -Uri "https://web-production-14aea.up.railway.app/webhooks/zapier/generate-post" -Method Post -Body $body -ContentType "application/json"
```

---

## 📊 Monitoring & Troubleshooting

### Check Zap History
1. Go to Zapier → Your Zap → **History**
2. View successful runs and any errors

### Common Issues

| Issue | Solution |
|-------|----------|
| Webhook timeout | API may be cold-starting, retry in 1 min |
| Empty text | Check content_type spelling |
| Buffer error | Reconnect Buffer account in Zapier |
| Rate limit | Free tier: 100 tasks/month, upgrade if needed |

### Verify API is Online
Visit: [https://web-production-14aea.up.railway.app](https://web-production-14aea.up.railway.app)

---

## 🚀 Next Steps

1. **Add media**: Integrate Imagen 3 or NanoBanana for auto-generated images
2. **Multi-platform**: Duplicate Zaps for Twitter/X and TikTok
3. **Analytics**: Track engagement and optimize content types
4. **Conditional logic**: Use Path by Zapier to vary content based on album_countdown

---

## 📅 Recommended Posting Schedule

| Time (WAT) | Content Type | Day |
|------------|--------------|-----|
| 7:00 AM | morning_blessing | Daily |
| 12:00 PM | music_wisdom | Mon-Fri |
| 3:00 PM | challenge_promo | Tue/Thu |
| 6:00 PM | album_promo | Wed/Sat |
| 9:00 PM | fan_appreciation | Friday |

---

**🎵 Add Value. We Flourish & Prosper. 🙏**

*THE VALUE ADDERS WAY: FLOURISH MODE - January 2026*

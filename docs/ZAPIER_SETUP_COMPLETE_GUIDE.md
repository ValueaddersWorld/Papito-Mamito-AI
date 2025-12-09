# Papito Mamito AI - Complete Zapier Setup Guide
## 3x Daily Automated Twitter Posts

**API Endpoint**: `https://web-production-14aea.up.railway.app`
**Budget**: 100 tweets/month → 3 posts/day × 30 days = 90 automated + 10 manual

---

## QUICK SETUP CHECKLIST

- [ ] Create Zap #1: Morning Post (7:00 AM WAT)
- [ ] Create Zap #2: Midday Post (1:00 PM WAT)  
- [ ] Create Zap #3: Evening Post (7:00 PM WAT)
- [ ] Test all 3 Zaps
- [ ] Turn on all Zaps

---

## ZAP #1: MORNING WISDOM (7:00 AM WAT)

### Step 1: Start New Zap
1. Go to https://zapier.com/app/editor
2. Click "Create" → "New Zap" (or use the + button)
3. Name your Zap: **"Papito Morning Post - 7AM"**

### Step 2: Set Up Trigger (Schedule)
1. Search for app: **Schedule by Zapier**
2. Select trigger event: **Every Day**
3. Click **Continue**
4. Configure schedule:
   - **Time of Day**: `7:00 am`
   - **Timezone**: Select `Africa/Lagos` (WAT) or `(UTC+01:00) West Africa Time`
5. Click **Continue**
6. Click **Test trigger** to verify
7. Click **Continue**

### Step 3: Add Action #1 (Webhook to Papito API)
1. Click the **+** button to add an action
2. Search for app: **Webhooks by Zapier**
3. Select event: **POST**
4. Click **Continue**
5. Configure the webhook:

   **URL:**
   ```
   https://web-production-14aea.up.railway.app/webhooks/zapier/generate-post
   ```

   **Payload Type:** `json`

   **Data (add these as separate rows):**
   | Key | Value |
   |-----|-------|
   | `content_type` | `morning_blessing` |
   | `include_album` | `true` |
   | `platform` | `twitter` |

   **Unflatten:** Yes
   **Headers:** (leave empty)

6. Click **Continue**
7. Click **Test action**
   - You should see a response with `success: true` and generated text
8. Click **Continue**

### Step 4: Add Action #2 (Post to Twitter)
1. Click the **+** button to add another action
2. Search for app: **Twitter** (or **X**)
3. Select event: **Create Tweet**
4. Click **Continue**
5. Connect your Twitter account if not already connected
   - Sign in with @PapitoMamito_ai credentials
6. Configure the tweet:

   **Message/Text:** Click the field, then:
   - Click **Insert Data** (the + icon)
   - Select from "2. POST in Webhooks": **text**
   - Add a line break (press Enter)
   - Click **Insert Data** again
   - Select: **hashtags**

   Your field should show something like:
   ```
   {{Step 2 - text}}

   {{Step 2 - hashtags}}
   ```

7. Click **Continue**
8. Click **Test action** to post a test tweet (optional - skip if you don't want to post now)
9. Click **Publish**

### Step 5: Turn On the Zap
1. Toggle the Zap **ON** at the top right
2. ✅ Zap #1 Complete!

---

## ZAP #2: MIDDAY INSIGHT (1:00 PM WAT)

**Repeat the exact same process as Zap #1, with these changes:**

- **Zap Name:** "Papito Midday Post - 1PM"
- **Time of Day:** `1:00 pm`
- **content_type:** `music_wisdom`

Everything else stays the same!

---

## ZAP #3: EVENING CONNECTION (7:00 PM WAT)

**Repeat the exact same process as Zap #1, with these changes:**

- **Zap Name:** "Papito Evening Post - 7PM"
- **Time of Day:** `7:00 pm`
- **content_type:** `fan_appreciation`

Everything else stays the same!

---

## CONTENT TYPE REFERENCE

| content_type | Best Time | Description |
|-------------|-----------|-------------|
| `morning_blessing` | 7:00 AM | Wisdom, intentions, morning motivation |
| `music_wisdom` | 1:00 PM | Insights about music, creativity, AI artistry |
| `fan_appreciation` | 7:00 PM | Gratitude, community connection |
| `album_promo` | Any | FLOURISH MODE countdown |
| `track_snippet` | Any | Studio updates, 50/50 creation story |
| `challenge_promo` | Any | #FlightMode6000 challenge |

---

## WEBHOOK CONFIGURATION DETAILS

**Full API Endpoint:**
```
https://web-production-14aea.up.railway.app/webhooks/zapier/generate-post
```

**Request Method:** POST

**Request Body (JSON):**
```json
{
  "content_type": "morning_blessing",
  "include_album": true,
  "platform": "twitter"
}
```

**Response Example:**
```json
{
  "success": true,
  "text": "Good morning. The richest currency isn't money—it's the positive impact you leave behind. New week, fresh energy. Let's set intentions that matter. Add Value. We Flourish & Prosper.",
  "hashtags": "#AddValue",
  "content_type": "morning_blessing",
  "platform": "twitter",
  "album_countdown": 36
}
```

---

## TIMEZONE REFERENCE

- **West Africa Time (WAT)** = UTC+1
- 7:00 AM WAT = 6:00 AM UTC = 7:00 AM CET
- 1:00 PM WAT = 12:00 PM UTC = 1:00 PM CET
- 7:00 PM WAT = 6:00 PM UTC = 7:00 PM CET

If you're in CET (Netherlands), the times align! WAT = CET.

---

## TESTING YOUR SETUP

After all 3 Zaps are created and turned on:

1. **Manual Test** - In Zapier, click "Run" on each Zap to test immediately
2. **Check Twitter** - Verify posts appear on @PapitoMamito_ai
3. **Monitor** - Check Zap History for any errors

### PowerShell Test Commands:
```powershell
# Test API directly
$body = @{
    content_type = "morning_blessing"
    include_album = $true
    platform = "twitter"
} | ConvertTo-Json

Invoke-RestMethod -Uri "https://web-production-14aea.up.railway.app/webhooks/zapier/generate-post" -Method Post -Body $body -ContentType "application/json"
```

---

## TROUBLESHOOTING

| Issue | Solution |
|-------|----------|
| Webhook timeout | API cold-starting, wait 1 min and retry |
| Empty text | Check content_type spelling |
| Twitter error | Reconnect Twitter account in Zapier |
| Rate limit | Free tier: 100 tasks/month |

---

## MONTHLY POST BUDGET

| Type | Count |
|------|-------|
| Morning Posts | 30 |
| Midday Posts | 30 |
| Evening Posts | 30 |
| **Total Automated** | **90** |
| Manual/Buffer | 10 |
| **Monthly Total** | **100** |

---

## PAPITO'S REFINED VOICE

The content now follows these guidelines:
- ✅ **Minimal emojis** (0-2 per post maximum)
- ✅ **1-2 hashtags only** (never more)
- ✅ **50% Human / 50% AI** music creation story
- ✅ Intelligent, substantive, wisdom-focused
- ✅ No spam, no fluff, pure value

---

**Add Value. We Flourish & Prosper.**

*THE VALUE ADDERS WAY: FLOURISH MODE - January 2026*

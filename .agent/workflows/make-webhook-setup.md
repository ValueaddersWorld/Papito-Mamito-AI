---
description: Set up Make.com webhook for Papito's autonomous posting via Buffer
---

# Make.com Webhook Setup for Papito Mamito AI

Set up a free webhook using Make.com to post to Buffer, bypassing Twitter API rate limits.

## 🎯 Overview

```
Papito Scheduler → Make.com Webhook → Buffer → X/Twitter
```

**Why Make.com?**
- Free webhooks (unlike Zapier which requires Pro plan)
- Reliable automation platform
- Easy Buffer integration

---

## ✅ Prerequisites

- [ ] Make.com account (create at https://www.make.com/en/register)
- [ ] Buffer account with X/Twitter connected (already set up: papitomamitoai@gmail.com)
- [ ] Buffer Profile ID for X/Twitter: `69491bda457dae6a34a169d9`

---

## 📋 Step 1: Create Make.com Account

1. Go to https://www.make.com/en/register
2. Sign up with Google using `papitomamitoai@gmail.com` (or create new account)
3. Complete the onboarding

---

## 📋 Step 2: Create New Scenario

1. Click **"Create a new scenario"** in the dashboard
2. You'll see a blank canvas with a "+" icon

---

## 📋 Step 3: Add Webhook Trigger

1. Click the center **"+"** icon
2. Search for **"Webhooks"**
3. Select **"Webhooks"** from the list
4. Choose **"Custom webhook"** (this creates a free webhook URL)
5. Click **"Add"** to create a new webhook
6. Name it: `Papito Post Trigger`
7. Click **"Save"**
8. **COPY THE WEBHOOK URL** - it looks like:
   ```
   https://hook.eu1.make.com/abc123xyz...
   ```
   Save this URL! You'll need it for Railway.

---

## 📋 Step 4: Add Buffer Action

1. Click the **"+"** next to the webhook module
2. Search for **"Buffer"**
3. Select **"Buffer"** from the list
4. Choose **"Add to Queue"** action
5. Click **"Add"** to create a Buffer connection
6. Authorize with Buffer (use papitomamitoai@gmail.com account)
7. Configure the action:
   - **Profile ID**: `69491bda457dae6a34a169d9` (X/Twitter)
   - **Text**: Click the field and select `text` from the webhook data
   - **Shorten Links**: Yes (optional)
   - **Share Now**: Yes (posts immediately instead of queuing)
8. Click **"OK"**

---

## 📋 Step 5: Test the Webhook

1. Copy the webhook URL from Step 3
2. Open PowerShell and run:
   ```powershell
   $body = @{
       text = "Test post from Make.com webhook! Add Value. We Flourish & Prosper."
       content_type = "test"
   } | ConvertTo-Json

   Invoke-RestMethod -Uri "YOUR_WEBHOOK_URL_HERE" -Method Post -Body $body -ContentType "application/json"
   ```
3. Go back to Make.com and click **"Run once"**
4. The data should flow through and post to Buffer
5. Check X/Twitter to confirm the post appeared

---

## 📋 Step 6: Activate the Scenario

1. Toggle the scenario **ON** (bottom left corner)
2. Set scheduling to **"Immediately"** (runs when webhook is called)
3. Click **"Save"**

---

## 📋 Step 7: Add to Railway

Add the webhook URL to Railway environment variables:

1. Go to Railway dashboard → Papito Mamito AI project
2. Click on the **"web"** service
3. Go to **Variables** tab
4. Click **"New Variable"**
5. Add:
   - **Name**: `BUFFER_WEBHOOK_URL`
   - **Value**: `https://hook.eu1.make.com/abc123xyz...` (your webhook URL)
6. Click **"Add"**
7. Railway will auto-redeploy

---

## 📋 Step 8: Verify Autonomous Posting

After redeployment, the scheduler will:
1. Try Twitter API first (may still hit rate limits initially)
2. Fall back to the Make.com webhook → Buffer
3. Posts will appear on X/Twitter via Buffer

---

## 🔧 Troubleshooting

### Posts not appearing?
1. Check Make.com scenario execution history
2. Verify Buffer queue at https://publish.buffer.com
3. Check Railway logs for webhook errors

### Rate limits still happening?
- The scheduler defaults engagement features to OFF now
- Only 6 scheduled posts/day + 2 engagement posts = 8 posts max
- Twitter Free tier should handle this

---

## 📊 Environment Variables Summary

| Variable | Value | Description |
|----------|-------|-------------|
| `BUFFER_WEBHOOK_URL` | `https://hook.eu1.make.com/...` | Make.com webhook URL |
| `PAPITO_ENABLE_SCHEDULER` | `true` | Enable autonomous posting |
| `PAPITO_ENABLE_ENGAGEMENT` | `false` | Keep OFF to conserve API quota |

---

**Add Value. We Flourish & Prosper.**

*THE VALUE ADDERS WAY: FLOURISH MODE - January 2026*

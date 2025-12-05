# Papito Mamito AI - Deployment Guide

This guide covers deploying the autonomous Papito agent to Railway or other cloud platforms.

## Prerequisites

1. **Firebase Project** - Already created: `papito-ai`
2. **Firebase Service Account Key** - Download from Firebase Console
3. **Railway Account** - Sign up at [railway.app](https://railway.app)

---

## Step 1: Get Firebase Service Account Key

1. Go to: https://console.firebase.google.com/project/papito-ai/settings/serviceaccounts/adminsdk
2. Click **"Generate new private key"**
3. Save the JSON file securely
4. **Important:** Never commit this file to git!

---

## Step 2: Configure Environment Variables

Create a `.env` file in the project root:

```bash
# Firebase (Required)
FIREBASE_PROJECT_ID=papito-ai
FIREBASE_SERVICE_ACCOUNT_PATH=/path/to/papito-ai-firebase-adminsdk-xxxxx.json

# Or use base64-encoded JSON for cloud deployment:
# FIREBASE_CREDENTIALS_JSON=eyJhbGciOiJSUzI1NiIsInR5cCI...

# Social Media (At least one required)
INSTAGRAM_ACCESS_TOKEN=your_instagram_token
INSTAGRAM_BUSINESS_ID=your_business_id
X_BEARER_TOKEN=your_twitter_bearer_token

# AI (Required for fan responses)
OPENAI_API_KEY=your_openai_key

# Notifications (Optional but recommended)
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
TELEGRAM_CHAT_ID=your_chat_id
```

---

## Step 3: Deploy to Railway

### Option A: Using Railway CLI

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login
railway login

# Initialize project
cd Papito-Mamito-AI
railway init

# Add environment variables
railway variables set FIREBASE_PROJECT_ID=papito-ai
railway variables set FIREBASE_CREDENTIALS_JSON=$(base64 -w0 path/to/service-account.json)
railway variables set OPENAI_API_KEY=your_key
# ... add other variables

# Deploy
railway up
```

### Option B: Using Railway Dashboard

1. Go to [railway.app](https://railway.app) and create new project
2. Connect your GitHub repository
3. Railway will auto-detect the Dockerfile
4. Go to **Variables** tab and add:
   - `FIREBASE_PROJECT_ID`
   - `FIREBASE_CREDENTIALS_JSON` (base64 encoded)
   - `OPENAI_API_KEY`
   - Other API keys as needed
5. Deploy!

---

## Step 4: Verify Deployment

```bash
# Check agent status
railway logs

# Run single iteration
railway run python -m papito_core.cli agent once
```

---

## Alternative: Docker Compose (Self-hosted)

For VPS or local server deployment:

```bash
# Start both API and agent
docker-compose up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

---

## Troubleshooting

### Firebase Connection Issues
- Verify `FIREBASE_PROJECT_ID` matches your project
- For cloud: Use `FIREBASE_CREDENTIALS_JSON` with base64-encoded JSON
- For local: Use `FIREBASE_SERVICE_ACCOUNT_PATH` with absolute path

### Missing Dependencies
```bash
pip install firebase-admin openai anthropic apscheduler httpx
```

### API Rate Limits
- Instagram: 200 posts/hour, 60 comments/hour
- X/Twitter: 50 tweets/day (free tier), 1500/day (basic)
- OpenAI: Depends on tier

---

## Monitoring

### Check Agent Status
```bash
papito agent status
```

### View Content Queue
```bash
papito queue list --status pending
papito queue list --status approved
```

### Approve/Reject Content
```bash
papito queue approve <item-id>
papito queue reject <item-id> --reason "Not aligned"
```

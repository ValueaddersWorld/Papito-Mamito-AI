# 🚀 Deploying Papito Mamito AI - True Autonomy

Papito needs to run 24/7 on a server to be truly autonomous. Here are your options:

## Option 1: Railway (Recommended - Free Tier Available)

1. Go to [railway.app](https://railway.app) and sign up
2. Click "New Project" → "Deploy from GitHub repo"
3. Select the `Papito-Mamito-AI` repository
4. In Settings:
   - Set the root directory to `/`
   - Use `Dockerfile.autonomous` as the Dockerfile
5. Add Environment Variables:
   ```
   OPENAI_API_KEY=your_openai_api_key
   TELEGRAM_BOT_TOKEN=your_telegram_bot_token
   TELEGRAM_OWNER_CHAT_ID=your_telegram_chat_id
   X_BEARER_TOKEN=your_bearer
   X_API_KEY=your_api_key
   X_API_SECRET=your_api_secret
   X_ACCESS_TOKEN=your_access_token
   X_ACCESS_TOKEN_SECRET=your_access_secret
   MOLTBOOK_API_KEY=your_moltbook_api_key
   ```
6. Deploy! Papito will run forever.

## Option 2: Render (Free Tier Available)

1. Go to [render.com](https://render.com) and sign up
2. Click "New" → "Background Worker"
3. Connect your GitHub repo
4. Configure:
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `python scripts/papito_autonomous_forever.py`
5. Add the same environment variables as above
6. Deploy!

## Option 3: Fly.io

```bash
# Install flyctl
curl -L https://fly.io/install.sh | sh

# Login
fly auth login

# Create app
fly launch --dockerfile Dockerfile.autonomous

# Set secrets
fly secrets set OPENAI_API_KEY=your_key
fly secrets set TELEGRAM_BOT_TOKEN=your_token
# ... add all other env vars

# Deploy
fly deploy
```

## Option 4: Any VPS (DigitalOcean, Linode, AWS, etc.)

```bash
# SSH to your server
ssh user@your-server

# Clone the repo
git clone https://github.com/ValueaddersWorld/Papito-Mamito-AI.git
cd Papito-Mamito-AI

# Create virtualenv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Create .env with your credentials
nano .env

# Run with screen/tmux for persistence
screen -S papito
python scripts/papito_autonomous_forever.py
# Press Ctrl+A, D to detach

# Or use systemd for auto-restart
sudo nano /etc/systemd/system/papito.service
```

Systemd service file (`/etc/systemd/system/papito.service`):
```ini
[Unit]
Description=Papito Mamito AI Autonomous Agent
After=network.target

[Service]
Type=simple
User=your_user
WorkingDirectory=/path/to/Papito-Mamito-AI
Environment=PATH=/path/to/Papito-Mamito-AI/venv/bin
ExecStart=/path/to/Papito-Mamito-AI/venv/bin/python scripts/papito_autonomous_forever.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Then:
```bash
sudo systemctl enable papito
sudo systemctl start papito
sudo systemctl status papito
```

## Required Environment Variables

| Variable | Description |
|----------|-------------|
| `OPENAI_API_KEY` | OpenAI API key for GPT-4 |
| `TELEGRAM_BOT_TOKEN` | Telegram bot token |
| `TELEGRAM_OWNER_CHAT_ID` | Your Telegram user ID |
| `X_BEARER_TOKEN` | X/Twitter bearer token |
| `X_API_KEY` | X/Twitter API key |
| `X_API_SECRET` | X/Twitter API secret |
| `X_ACCESS_TOKEN` | X/Twitter access token |
| `X_ACCESS_TOKEN_SECRET` | X/Twitter access token secret |
| `PAPITO_X_READ_ENABLED` | Set `true` after X API credits are funded |
| `PAPITO_X_LIVE_ENGAGEMENT` | Set `true` to run the independent mention listener |
| `PAPITO_X_AI_REPLY_APPROVED` | Set `true` only after written X approval for the AI reply bot |
| `PAPITO_X_POLL_SECONDS` | Mention polling interval; `180` is the recommended starting point |
| `PAPITO_X_MAX_REPLIES_PER_DAY` | Daily quality and safety cap; start with `12` |
| `PAPITO_X_STATE_FILE` | Use `/app/data/x_live_conversations.json` on Railway |
| `PAPITO_POST_MEMORY_FILE` | Use `/app/data/post_memory.json` on Railway |

## Enable Live X Conversations

X API access is pay-per-usage. Fund API credits in the X Developer Console,
confirm the app has read and write permissions, then regenerate the user access
token after changing permissions.

X requires prior written approval before operating an AI-powered automated reply
bot. Request approval in the developer portal and keep
`PAPITO_X_AI_REPLY_APPROVED=false` until it is granted.

In Railway, attach a persistent Volume mounted at `/app/data`. This keeps
conversation memory, processed mention IDs, opt-outs, and post memory across
deployments. Run exactly one autonomous worker replica so two workers cannot
reply to the same interaction.

After credits and approval are confirmed, set:

```env
PAPITO_X_READ_ENABLED=true
PAPITO_X_LIVE_ENGAGEMENT=true
PAPITO_X_AI_REPLY_APPROVED=true
PAPITO_X_POLL_SECONDS=180
PAPITO_X_MAX_REPLIES_PER_DAY=12
PAPITO_X_STATE_FILE=/app/data/x_live_conversations.json
PAPITO_POST_MEMORY_FILE=/app/data/post_memory.json
```

## Verifying Papito is Running

After deployment, Papito will:
1. Send you a Telegram message confirming startup
2. Create/join communities on Moltbook
3. Follow interesting agents
4. Post original X content during Amsterdam daytime windows
5. Poll direct X mentions independently of the posting schedule
6. Reply contextually when live engagement is approved and enabled
7. Continue operating autonomously forever

Check logs on your platform to see his activity!

---
**Add Value. We Flourish & Prosper.** ✨

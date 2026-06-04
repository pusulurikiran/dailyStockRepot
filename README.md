# 🇮🇳 Indian Stock Market Telegram Bot

A Claude-powered Telegram bot that delivers daily NSE/BSE swing-trade reports
every morning at **08:30 IST (Mon–Fri)** and responds to on-demand queries 24×7.

---

## Features

| Command | What you get |
|---------|-------------|
| `/report` | Full daily report — macro + 10 stock ideas with entry/target/stop |
| `/quick` | Top 5 picks, one line each |
| `/macro` | Nifty levels, crude, FII/DII flows, VIX |
| `/sector` | Sector rotation theme + smart-money accumulation |
| Free text | Your question answered by Claude Opus as your personal analyst |

---

## Quick Start

### 1. Get a Telegram Bot Token

1. Open Telegram and search for **@BotFather**.
2. Send `/newbot` and follow the prompts.
3. Copy the token — it looks like `7123456789:AAFxxxxxxxxxxxxxxxxxxxxxx`.

### 2. Get Your Telegram Chat ID

**Method A — via the bot itself:**
1. Start your new bot (send `/start`).
2. Visit this URL in your browser (replace `<TOKEN>`):
   ```
   https://api.telegram.org/bot<TOKEN>/getUpdates
   ```
3. Look for `"chat":{"id": 123456789 …}` — that number is your Chat ID.

**Method B — use @userinfobot:**
1. Search for **@userinfobot** on Telegram.
2. Send `/start` — it replies with your numeric ID.

### 3. Get an Anthropic API Key

1. Go to <https://console.anthropic.com>.
2. Create an API key under **API Keys**.

---

## GitHub Actions Setup (Scheduled Daily Report)

### Add Secrets

In your GitHub repo: **Settings → Secrets and variables → Actions → New repository secret**

| Secret name | Value |
|-------------|-------|
| `ANTHROPIC_API_KEY` | Your Anthropic key |
| `TELEGRAM_TOKEN` | Your bot token from BotFather |
| `CHAT_ID` | Your numeric Telegram chat ID |

### Push the Code

```bash
git init
git add .
git commit -m "Initial stock bot"
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git
git push -u origin main
```

The workflow at `.github/workflows/stock-bot.yml` will fire automatically
**Monday–Friday at 03:00 UTC (08:30 IST)**.

### Manual Test Run

Go to **Actions → Indian Stock Market Bot → Run workflow** — leave mode as
`scheduled` and click **Run workflow**.

---

## Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export ANTHROPIC_API_KEY="sk-ant-..."
export TELEGRAM_TOKEN="7123456789:AAF..."
export CHAT_ID="123456789"

# Send a scheduled report right now
python daily_report.py

# Reply to a specific chat (used internally by bot_polling.py)
python daily_report.py --webhook 123456789 "/quick"

# Start the interactive polling bot
python bot_polling.py
```

---

## Always-On Interactive Bot — Deploy to Railway

GitHub Actions times out after 6 hours and is billed per minute — not suitable
for continuous polling. Use **Railway** (free tier) instead.

### Steps

1. **Sign up** at <https://railway.app> (GitHub login works).

2. **New Project → Deploy from GitHub Repo** — select this repo.

3. **Add environment variables** in Railway's dashboard:
   - `ANTHROPIC_API_KEY`
   - `TELEGRAM_TOKEN`
   - `CHAT_ID`

4. **Set the start command** (Railway → Settings → Deploy → Start Command):
   ```
   python bot_polling.py
   ```

5. **Deploy** — Railway will keep the process running 24×7 and auto-restart
   on crashes.

### Alternative: Render.com

1. New Web Service → connect GitHub repo.
2. Build command: `pip install -r requirements.txt`
3. Start command: `python bot_polling.py`
4. Add the three env vars under **Environment**.
5. Deploy — free tier keeps it alive.

---

## File Structure

```
stockReport/
├── daily_report.py              # Core bot — both scheduled & webhook mode
├── bot_polling.py               # Always-on polling loop
├── requirements.txt
├── README.md
└── .github/
    └── workflows/
        └── stock-bot.yml        # GitHub Actions cron + optional polling job
```

---

## Command Reference

| Input | Behaviour |
|-------|-----------|
| `/start` or `/help` | Show help menu |
| `/report` | Full 10-stock daily report with macro |
| `/quick` | Top 5 picks — entry / target / stop one-liner |
| `/macro` | Nifty, crude, FII/DII, VIX, events |
| `/sector` | Sector rotation theme, smart-money flows |
| Any other text | Passed directly to Claude as a custom query |

---

## Model & Cost

- Model: `claude-opus-4-6`
- Max tokens per response: `2000`
- Estimated cost per full report: ~$0.05–0.10 (varies by input length)
- Daily scheduled cost: < $0.15/day

---

## Disclaimer

This bot provides information for educational purposes only. It is **not**
SEBI-registered investment advice. Always do your own research before trading.

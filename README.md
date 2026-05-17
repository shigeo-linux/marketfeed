# Marketfeed

Market data sent to your Telegram chat on a schedule. Every morning (and optionally evening) get a snapshot of major indices, gold, silver, bitcoin, and the 10-year US Treasury yield.

No API key needed — data is sourced from Yahoo Finance for free.

---

## What you get

```
📈 Marketfeed — Morning Briefing
📅 Monday 19 May 2026

📊 Markets
📈 S&P 500: $5,321.41  ▲ 0.42%
📈 Dow Jones: $42,156.20  ▼ 1.07%
📈 Nasdaq: $16,842.11  ▲ 0.89%
🥇 Gold: $2,341.50/oz  ▲ 0.31%
🥈 Silver: $27.82/oz  ▲ 0.51%
₿ Bitcoin: $68,450.00  ▲ 2.10%
🏦 10Y Treasury: 4.42%  ▼ 0.05%

🕐 Marketfeed — 07:00 on 19 May 2026
```

---

## Features

- **Morning and optional evening briefings** at your chosen times
- **Runs automatically** via systemd timer every hour
- **Send Now button** to trigger a briefing on demand
- **No API key required** — uses Yahoo Finance

---

## Requirements

- Ubuntu 24.04 / Linux Mint 22.x (or any systemd-based Linux)
- Python 3.10+
- A Telegram bot token and chat ID

---

## Installation

```bash
cd marketfeed/
chmod +x install.sh
./install.sh
```

Then launch:
```bash
marketfeed
```

---

## Setup

1. Launch Marketfeed
2. Enter your **Telegram bot token** and **chat ID**
3. Set your **morning briefing hour** (24h — e.g. `7` for 7:00am)
4. Optionally set an **evening hour** (`-1` to disable)
5. Click **Save Settings**
6. Click **Send Briefing Now** to test

### Getting a Telegram bot

1. Open Telegram and search for **@BotFather**
2. Send `/newbot` and follow the prompts to get your bot token
3. Start a chat with your bot, send any message
4. Visit `https://api.telegram.org/botYOUR_TOKEN/getUpdates` to find your chat ID

---

## Market data tracked

| Symbol | Name |
|---|---|
| ^GSPC | S&P 500 |
| ^DJI | Dow Jones |
| ^IXIC | Nasdaq |
| GC=F | Gold |
| SI=F | Silver |
| BTC-USD | Bitcoin |
| ^TNX | 10-Year US Treasury Yield |

---

## Managing the timer

```bash
systemctl --user status marketfeed.timer
systemctl --user stop marketfeed.timer
systemctl --user disable marketfeed.timer
```

---

## Data storage

| Data | Location |
|---|---|
| Settings | `~/.config/marketfeed/config.json` |
| Activity log | `~/.config/marketfeed/marketfeed.log` |

---

## Uninstall

```bash
systemctl --user stop marketfeed.timer
systemctl --user disable marketfeed.timer
rm ~/.config/systemd/user/marketfeed.*
sudo rm -rf /opt/marketfeed
sudo rm -f /usr/local/bin/marketfeed
sudo rm -f /usr/share/applications/marketfeed.desktop
sudo rm -f /usr/share/icons/hicolor/scalable/apps/marketfeed.svg
rm -rf ~/.config/marketfeed
```

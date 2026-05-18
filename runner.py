#!/usr/bin/env python3
import sys
import os
import datetime
import logging

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import Config, LOG_FILE, CONFIG_DIR
from market_data import fetch_market_data, format_market_block
from summarizer import build_full_briefing
from telegram_client import send_message, TelegramError

os.makedirs(CONFIG_DIR, exist_ok=True)

logging.basicConfig(
    filename=LOG_FILE, level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s',
)


def run():
    config = Config()
    now = datetime.datetime.now()
    now_str = now.isoformat(sep=' ', timespec='seconds')
    today = now.strftime('%Y-%m-%d')

    edition = None
    sent_key = None
    if now.hour == config.morning_hour and config.get('last_morning_sent') != today:
        edition, sent_key = 'Morning', 'last_morning_sent'
    elif config.evening_hour >= 0 and now.hour == config.evening_hour and config.get('last_evening_sent') != today:
        edition, sent_key = 'Evening', 'last_evening_sent'

    if not edition:
        config.set('last_run', now_str)
        config.set('last_status', f'OK — checked at {now.strftime("%H:%M")}, not send time')
        config.save()
        return

    try:
        logging.info(f"Starting {edition} briefing")
        market_data = fetch_market_data()
        market_block = format_market_block(market_data)
        message = build_full_briefing(market_block, edition=edition)
        send_message(config.telegram_token, config.telegram_chat_id, message)

        config.set(sent_key, today)
        config.set('last_run', now_str)
        config.set('last_status', f'OK — {edition} briefing sent')
        config.save()
        logging.info(f"{edition} briefing sent")

    except TelegramError as e:
        msg = f'Telegram error: {str(e)[:120]}'
        logging.error(msg)
        config.set('last_run', now_str)
        config.set('last_status', f'Error: {msg}')
        config.save()
        sys.exit(1)

    except Exception as e:
        msg = str(e)[:120]
        logging.error(f"Error: {msg}")
        config.set('last_run', now_str)
        config.set('last_status', f'Error: {msg}')
        config.save()
        sys.exit(1)


if __name__ == '__main__':
    run()

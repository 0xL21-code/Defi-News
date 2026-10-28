"""Schickt neue DeFi/Crypto-News als Links per Telegram. Kostenlos, ohne KI."""
import json
import os
import time
from pathlib import Path

import feedparser
import requests

FEEDS = [
    "https://www.coindesk.com/arc/outboundfeeds/rss/",
    "https://cointelegraph.com/rss",
    "https://www.theblock.co/rss.xml",
    "https://decrypt.co/feed",
    "https://www.dlnews.com/arc/outboundfeeds/rss/",
    "https://rekt.news/rss.xml",
]

# "Wichtig"-Filter: Artikel muss mindestens ein Stichwort im Titel haben.
# Leere Liste = ALLE Artikel senden (kann viel sein).
KEYWORDS = [
    "hack", "exploit", "stolen", "drained", "rug", "depeg",
    "sec", "etf", "regulat", "ban", "lawsuit", "approval", "mica",
    "bitcoin", "btc", "ethereum", "eth", "solana", "stablecoin", "usdt", "usdc",
    "defi", "aave", "uniswap", "lido", "maker", "sky", "curve", "hyperliquid",
    "binance", "coinbase", "tether", "blackrock", "fed", "listing", "airdrop",
    "upgrade", "mainnet", "outage", "bankrupt",
]

MAX_PER_RUN = 20
SEEN_FILE = Path("seen.json")
TOKEN = os.environ["TELEGRAM_TOKEN"]
CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]


def load_seen():
    if SEEN_FILE.exists():
        return json.loads(SEEN_FILE.read_text())
    return None


def send(text):
    r = requests.post(
        f"https://api.telegram.org/bot{TOKEN}/sendMessage",
        json={"chat_id": CHAT_ID, "text": text},
        timeout=20,
    )
    r.raise_for_status()


def matches(title):
    if not KEYWORDS:
        return True
    t = title.lower()
    return any(k in t for k in KEYWORDS)


def main():
    seen = load_seen()
    first_run = seen is None
    seen = seen or []
    seen_set = set(seen)
    new_items = []

    for url in FEEDS:
        try:
            feed = feedparser.parse(url)
        except Exception as e:
            print("Feed-Fehler", url, e)
            continue
        source = feed.feed.get("title", url)
        for e in feed.entries:
            uid = e.get("id") or e.get("link")
            if not uid or uid in seen_set:
                continue
            seen_set.add(uid)
            seen.append(uid)
            if matches(e.get("title", "")):
                new_items.append((source, e.get("title", ""), e.get("link", "")))

    # Beim ersten Lauf nur merken, nichts senden (sonst Nachrichten-Flut)
    if not first_run:
        for source, title, link in new_items[:MAX_PER_RUN]:
            send(f"{title}\n{source}\n{link}")
            time.sleep(0.5)

    SEEN_FILE.write_text(json.dumps(seen[-5000:]))


if __name__ == "__main__":
    main()

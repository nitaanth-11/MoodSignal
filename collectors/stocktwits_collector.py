"""
StockTwits Data Collector
=========================
Fetches recent messages from StockTwits for configured symbols using
browser-compatible headers to access the public API.

Outputs rows to data/raw_posts.csv with columns:
    text, timestamp, source, subreddit, score, num_comments
(subreddit column is repurposed as 'symbol' for StockTwits data)
"""

import sys
import time
import logging
from datetime import datetime, timezone

import pandas as pd
import requests

try:
    from curl_cffi import requests as requests_cffi
    HAS_CFFI = True
except ImportError:
    HAS_CFFI = False
    requests_cffi = None

sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent.parent))
import config

logger = logging.getLogger(__name__)

# Browser-like headers to avoid 403 blocks
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/126.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/html,*/*",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://stocktwits.com/",
}

MESSAGES_ENDPOINT = "{base}/streams/symbol/{symbol}.json"
REQUEST_DELAY = 1.5


def collect(max_per_symbol: int = 30) -> pd.DataFrame:
    """
    Fetch recent StockTwits messages for configured symbols.

    Parameters
    ----------
    max_per_symbol : int
        Max messages to keep per symbol (API returns up to 30 per call).

    Returns
    -------
    pd.DataFrame
        Collected messages with standardised columns.
    """
    rows = []

    for symbol in config.STOCKTWITS_SYMBOLS:
        url = MESSAGES_ENDPOINT.format(base=config.STOCKTWITS_BASE_URL, symbol=symbol)
        logger.info(f"Fetching StockTwits messages for ${symbol}...")

        try:
            if HAS_CFFI:
                resp = requests_cffi.get(url, impersonate="chrome120", timeout=15)
            else:
                resp = requests.get(url, headers=HEADERS, timeout=15)

                if resp.status_code == 403:
                    logger.warning(f"  403 on ${symbol} -- retrying with delay...")
                    time.sleep(5)
                    resp = requests.get(url, headers=HEADERS, timeout=15)

                if resp.status_code == 429:
                    wait = int(resp.headers.get("Retry-After", 15))
                    logger.warning(f"  Rate limited -- waiting {wait}s...")
                    time.sleep(wait)
                    resp = requests.get(url, headers=HEADERS, timeout=15)

            resp.raise_for_status()
            data = resp.json()

            messages = data.get("messages", [])
            for msg in messages[:max_per_symbol]:
                body = msg.get("body", "").strip()
                if not body:
                    continue

                # Parse timestamp
                created = msg.get("created_at", "")
                try:
                    ts = datetime.strptime(
                        created, "%Y-%m-%dT%H:%M:%SZ"
                    ).replace(tzinfo=timezone.utc).isoformat()
                except (ValueError, TypeError):
                    ts = datetime.now(timezone.utc).isoformat()

                rows.append({
                    "text": body[:500].replace("\n", " "),
                    "timestamp": ts,
                    "source": "stocktwits",
                    "subreddit": symbol,  # reuse column for symbol
                    "score": msg.get("likes", {}).get("total", 0) if isinstance(msg.get("likes"), dict) else 0,
                    "num_comments": msg.get("conversation", {}).get("replies", 0) if isinstance(msg.get("conversation"), dict) else 0,
                })

            logger.info(f"  ${symbol}: {len([r for r in rows if r.get('subreddit') == symbol])} messages")

        except requests.exceptions.RequestException as e:
            logger.warning(f"  Error fetching StockTwits ${symbol}: {e}")
            continue

        time.sleep(REQUEST_DELAY)

    df = pd.DataFrame(rows)
    logger.info(f"Total StockTwits messages collected: {len(df)}")
    return df


def save(df: pd.DataFrame, append: bool = True) -> None:
    """Save collected data to the raw posts CSV."""
    if df.empty:
        logger.warning("No StockTwits data to save.")
        return

    if append and config.RAW_POSTS_CSV.exists():
        existing = pd.read_csv(config.RAW_POSTS_CSV)
        df = pd.concat([existing, df], ignore_index=True)
        df.drop_duplicates(subset=["text", "timestamp"], inplace=True)

    df.to_csv(config.RAW_POSTS_CSV, index=False)
    logger.info(f"Saved {len(df)} total rows -> {config.RAW_POSTS_CSV}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
    data = collect()
    save(data)

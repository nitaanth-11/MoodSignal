"""
Reddit Data Collector
=====================
Scrapes posts and comments from financial subreddits using PRAW
(Python Reddit API Wrapper). Requires Reddit API credentials in .env.

If credentials are not configured, the collector is skipped gracefully
and the pipeline continues with StockTwits data only.

Outputs rows to data/raw_posts.csv with columns:
    text, timestamp, source, subreddit, score, num_comments
"""

import sys
import logging
from datetime import datetime, timezone

import pandas as pd

sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent.parent))
import config

logger = logging.getLogger(__name__)


def _has_credentials() -> bool:
    """Check if Reddit API credentials are configured."""
    return bool(
        config.REDDIT_CLIENT_ID
        and config.REDDIT_CLIENT_ID != "your_client_id_here"
        and config.REDDIT_CLIENT_SECRET
        and config.REDDIT_CLIENT_SECRET != "your_client_secret_here"
    )


def collect(limit_per_sub: int = 50, include_comments: bool = True) -> pd.DataFrame:
    """
    Scrape recent posts from configured subreddits using PRAW.

    Parameters
    ----------
    limit_per_sub : int
        Max posts to fetch per subreddit (default 50).
    include_comments : bool
        Also collect top-level comments from each post.

    Returns
    -------
    pd.DataFrame of collected posts/comments.
    """
    if not _has_credentials():
        logger.warning(
            "Reddit API credentials not configured. "
            "Set REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET in .env "
            "(see .env.example). Skipping Reddit collection."
        )
        return pd.DataFrame()

    try:
        import praw
    except ImportError:
        logger.warning("praw not installed. Run: pip install praw")
        return pd.DataFrame()

    reddit = praw.Reddit(
        client_id=config.REDDIT_CLIENT_ID,
        client_secret=config.REDDIT_CLIENT_SECRET,
        user_agent=config.REDDIT_USER_AGENT,
    )

    rows = []
    for sub_name in config.SUBREDDITS:
        logger.info(f"  r/{sub_name} (limit={limit_per_sub})...")

        try:
            subreddit = reddit.subreddit(sub_name)

            # Fetch hot posts
            for submission in subreddit.hot(limit=limit_per_sub):
                text = submission.title
                if submission.selftext:
                    text += f" {submission.selftext[:500]}"

                rows.append({
                    "text": text.replace("\n", " ").strip(),
                    "timestamp": datetime.fromtimestamp(
                        submission.created_utc, tz=timezone.utc
                    ).isoformat(),
                    "source": "reddit",
                    "subreddit": sub_name,
                    "score": submission.score,
                    "num_comments": submission.num_comments,
                })

                # Top-level comments
                if include_comments:
                    submission.comments.replace_more(limit=0)
                    for comment in submission.comments[:5]:
                        if not comment.body or comment.body in ("[deleted]", "[removed]"):
                            continue
                        rows.append({
                            "text": comment.body[:500].replace("\n", " ").strip(),
                            "timestamp": datetime.fromtimestamp(
                                comment.created_utc, tz=timezone.utc
                            ).isoformat(),
                            "source": "reddit",
                            "subreddit": sub_name,
                            "score": comment.score,
                            "num_comments": 0,
                        })

            logger.info(f"  r/{sub_name}: collected {len([r for r in rows if r.get('subreddit') == sub_name])} rows")

        except Exception as e:
            logger.warning(f"  Error scraping r/{sub_name}: {e}")
            continue

    df = pd.DataFrame(rows)

    if not df.empty:
        df = df[df["text"].str.strip().astype(bool)].reset_index(drop=True)
        df.drop_duplicates(subset=["text", "timestamp"], inplace=True)

    logger.info(f"Total Reddit posts collected: {len(df)}")
    return df


def save(df: pd.DataFrame, append: bool = True) -> None:
    """Save collected data to the raw posts CSV."""
    if df.empty:
        logger.warning("No Reddit data to save (credentials not set or no posts found).")
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

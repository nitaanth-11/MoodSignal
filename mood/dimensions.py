"""
Mood Dimensions
===============
Aggregates individual post sentiment scores into 5 daily mood dimensions:

    Calm     — inverse of sentiment volatility (high calm = low variance)
    Fear     — proportion of strongly negative posts + keyword boost
    Optimism — mean positive score weighted by engagement
    Anxiety  — blend of fear and volatility signals
    Happy    — proportion of strongly positive posts + keyword boost

Reads data/scored_posts.csv → outputs data/daily_mood.csv
"""

import sys
import logging

import pandas as pd
import numpy as np

sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent.parent))
import config

logger = logging.getLogger(__name__)


def _keyword_boost(texts: pd.Series, keywords: list[str]) -> float:
    """
    Calculate what fraction of texts contain at least one keyword.

    Returns float between 0 and 1.
    """
    if texts.empty:
        return 0.0

    lower_texts = texts.str.lower()
    matches = lower_texts.apply(
        lambda t: any(kw in str(t) for kw in keywords)
    )
    return matches.mean()


def _compute_dimensions(group: pd.DataFrame) -> dict:
    """
    Compute the 5 mood dimensions for a single day's worth of posts.

    Parameters
    ----------
    group : pd.DataFrame
        All scored posts for one day.

    Returns
    -------
    dict with keys: calm, fear, optimism, anxiety, happy (each 0-1)
    """
    scores = group["sentiment_score"].astype(float)
    texts = group["text"].fillna("")

    # Engagement weight: log(score + 2) to dampen extreme upvotes
    engagement = np.log1p(group["score"].fillna(0).clip(lower=0) + 1)
    engagement_weights = engagement / engagement.sum() if engagement.sum() > 0 else None

    # ── Calm: inverse of sentiment volatility ────────────────────────
    std = scores.std()
    calm = float(np.clip(1.0 - (std / 1.0), 0, 1))  # std of [-1,1] is max ~1

    # ── Fear: proportion strongly negative + keyword boost ───────────
    strongly_neg = (scores < -0.3).mean()
    fear_keywords = _keyword_boost(texts, config.FEAR_KEYWORDS)
    fear = float(np.clip(0.6 * strongly_neg + 0.4 * fear_keywords, 0, 1))

    # ── Optimism: weighted mean of positive scores ───────────────────
    positive_mask = scores > 0
    if positive_mask.any() and engagement_weights is not None:
        weighted_pos = np.average(
            scores[positive_mask],
            weights=engagement_weights[positive_mask],
        )
        optimism = float(np.clip(weighted_pos, 0, 1))
    else:
        optimism = float(np.clip(scores.mean(), 0, 1)) if scores.mean() > 0 else 0.0

    # ── Anxiety: blend of fear + volatility ──────────────────────────
    anxiety = float(np.clip(0.5 * fear + 0.5 * (1 - calm), 0, 1))

    # ── Happy: proportion strongly positive + keyword boost ──────────
    strongly_pos = (scores > 0.3).mean()
    happy_keywords = _keyword_boost(texts, config.HAPPY_KEYWORDS)
    happy = float(np.clip(0.6 * strongly_pos + 0.4 * happy_keywords, 0, 1))

    return {
        "calm": round(calm, 4),
        "fear": round(fear, 4),
        "optimism": round(optimism, 4),
        "anxiety": round(anxiety, 4),
        "happy": round(happy, 4),
    }


def compute_daily_mood() -> pd.DataFrame:
    """
    Aggregate scored posts into daily mood dimensions.

    Returns
    -------
    pd.DataFrame with columns: date, calm, fear, optimism, anxiety, happy
    """
    if not config.SCORED_POSTS_CSV.exists():
        logger.error(f"No scored posts found at {config.SCORED_POSTS_CSV}")
        return pd.DataFrame()

    df = pd.read_csv(config.SCORED_POSTS_CSV)

    # Parse timestamp to date
    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True, errors="coerce")
    df["date"] = df["timestamp"].dt.date

    logger.info(f"Computing mood dimensions for {df['date'].nunique()} days...")

    daily = []
    for date, group in df.groupby("date"):
        if len(group) < 2:
            continue  # need at least 2 posts for meaningful stats
        dims = _compute_dimensions(group)
        dims["date"] = str(date)
        daily.append(dims)

    result = pd.DataFrame(daily)

    if not result.empty:
        result = result.sort_values("date").reset_index(drop=True)
        result.to_csv(config.DAILY_MOOD_CSV, index=False)
        logger.info(f"Saved daily mood to {config.DAILY_MOOD_CSV} ({len(result)} days)")
    else:
        logger.warning("No daily mood data computed (insufficient posts).")

    return result


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
    compute_daily_mood()

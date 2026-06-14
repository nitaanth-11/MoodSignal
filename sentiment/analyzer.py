"""
Sentiment Analyzer
==================
Dual-engine sentiment scoring using FinBERT and VADER.

- FinBERT: Fine-tuned BERT for financial text → positive/negative/neutral
- VADER:   Lexicon-based → compound score (-1 to +1)
- Combined: Weighted ensemble score

Reads data/raw_posts.csv → outputs data/scored_posts.csv
"""

import sys
import logging

import pandas as pd
import numpy as np

sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent.parent))
import config

logger = logging.getLogger(__name__)


class SentimentAnalyzer:
    """Combines FinBERT and VADER for financial sentiment analysis."""

    def __init__(self, use_finbert: bool = True):
        """
        Parameters
        ----------
        use_finbert : bool
            If True, load the FinBERT transformer model.
            Set False for faster (VADER-only) analysis.
        """
        self._finbert_pipeline = None
        self._vader = None
        self._use_finbert = use_finbert

        self._init_vader()
        if use_finbert:
            self._init_finbert()

    def _init_vader(self):
        """Initialise VADER sentiment analyzer."""
        from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
        self._vader = SentimentIntensityAnalyzer()
        logger.info("VADER initialised")

    def _init_finbert(self):
        """Load FinBERT model from Hugging Face."""
        try:
            from transformers import pipeline
            logger.info(f"Loading FinBERT model ({config.FINBERT_MODEL})...")
            self._finbert_pipeline = pipeline(
                "sentiment-analysis",
                model=config.FINBERT_MODEL,
                tokenizer=config.FINBERT_MODEL,
                truncation=True,
                max_length=512,
            )
            logger.info("FinBERT loaded successfully")
        except Exception as e:
            logger.warning(f"Could not load FinBERT: {e}. Falling back to VADER only.")
            self._use_finbert = False

    def score_vader(self, text: str) -> dict:
        """
        Get VADER sentiment scores for a single text.

        Returns
        -------
        dict with keys: vader_compound, vader_pos, vader_neg, vader_neu
        """
        scores = self._vader.polarity_scores(text)
        return {
            "vader_compound": scores["compound"],
            "vader_pos": scores["pos"],
            "vader_neg": scores["neg"],
            "vader_neu": scores["neu"],
        }

    def score_finbert(self, text: str) -> dict:
        """
        Get FinBERT sentiment scores for a single text.

        Returns
        -------
        dict with keys: finbert_label, finbert_score
            label: 'positive', 'negative', or 'neutral'
            score: confidence (0-1)
        """
        if self._finbert_pipeline is None:
            return {"finbert_label": "neutral", "finbert_score": 0.0}

        try:
            result = self._finbert_pipeline(text[:512])[0]
            return {
                "finbert_label": result["label"],
                "finbert_score": result["score"],
            }
        except Exception as e:
            logger.debug(f"FinBERT error: {e}")
            return {"finbert_label": "neutral", "finbert_score": 0.0}

    def combined_score(self, text: str) -> dict:
        """
        Compute combined sentiment score from both engines.

        Returns all individual scores plus a unified `sentiment_score` (-1 to +1).
        """
        vader = self.score_vader(text)
        finbert = self.score_finbert(text)

        # Map FinBERT label to numeric (-1, 0, +1)
        finbert_numeric = {
            "positive": 1.0,
            "negative": -1.0,
            "neutral": 0.0,
        }.get(finbert["finbert_label"], 0.0)

        # Weight by confidence
        finbert_value = finbert_numeric * finbert["finbert_score"]

        # Weighted combination
        if self._use_finbert:
            combined = (
                config.FINBERT_WEIGHT * finbert_value
                + config.VADER_WEIGHT * vader["vader_compound"]
            )
        else:
            combined = vader["vader_compound"]

        return {
            **vader,
            **finbert,
            "sentiment_score": round(combined, 4),
        }


def analyze(use_finbert: bool = True) -> pd.DataFrame:
    """
    Score all posts in raw_posts.csv and save results.

    Parameters
    ----------
    use_finbert : bool
        Whether to use FinBERT (slower but more accurate for financial text).

    Returns
    -------
    pd.DataFrame with sentiment columns appended.
    """
    if not config.RAW_POSTS_CSV.exists():
        logger.error(f"No raw posts found at {config.RAW_POSTS_CSV}")
        return pd.DataFrame()

    df = pd.read_csv(config.RAW_POSTS_CSV)
    logger.info(f"Scoring {len(df)} posts...")

    analyzer = SentimentAnalyzer(use_finbert=use_finbert)

    results = []
    for i, row in df.iterrows():
        text = str(row.get("text", ""))
        scores = analyzer.combined_score(text)
        results.append(scores)

        if (i + 1) % 50 == 0:
            logger.info(f"  Scored {i + 1}/{len(df)} posts")

    scores_df = pd.DataFrame(results)
    df = pd.concat([df.reset_index(drop=True), scores_df], axis=1)

    df.to_csv(config.SCORED_POSTS_CSV, index=False)
    logger.info(f"Saved scored posts to {config.SCORED_POSTS_CSV}")
    return df


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
    analyze(use_finbert=True)

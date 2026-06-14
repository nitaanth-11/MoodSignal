"""
XGBoost Trainer
===============
Trains an XGBoost binary classifier to predict next-day DJIA direction
(1 = up, 0 = down) using mood + price features.

Reads: data/features.csv
Outputs: models/xgb_model.json + performance metrics to stdout
"""

import sys
import logging
import json

import pandas as pd
import numpy as np
from sklearn.model_selection import TimeSeriesSplit
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    precision_score,
    recall_score,
    confusion_matrix,
    classification_report,
)
import xgboost as xgb

sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent.parent))
import config

logger = logging.getLogger(__name__)

# Columns to exclude from features
EXCLUDE_COLS = {"date", "next_day_direction", "direction", "open", "high", "low", "close", "volume"}


def get_feature_target(df: pd.DataFrame):
    """Split DataFrame into feature matrix X and target y."""
    feature_cols = [c for c in df.columns if c not in EXCLUDE_COLS]
    X = df[feature_cols].astype(float)
    y = df["next_day_direction"].astype(int)
    return X, y, feature_cols


def train() -> dict:
    """
    Train XGBoost model with chronological train/test split.

    Handles edge cases:
    - Single-class data: saves a naive model that always predicts the majority class
    - Very small data (<5 rows): trains on all data with a warning

    Returns
    -------
    dict with keys: accuracy, f1, precision, recall, feature_importance
    """
    if not config.FEATURES_CSV.exists():
        logger.error(f"Feature file not found: {config.FEATURES_CSV}")
        return {}

    df = pd.read_csv(config.FEATURES_CSV)
    X, y, feature_cols = get_feature_target(df)

    logger.info(f"Training data: {X.shape[0]} samples, {X.shape[1]} features")
    logger.info(f"Class balance: {y.value_counts().to_dict()}")

    n_classes = y.nunique()

    # -- Single-class edge case ----------------------------------------
    if n_classes < 2:
        majority = int(y.mode()[0])
        label = "UP" if majority == 1 else "DOWN"
        logger.warning(
            f"Only one class ({label}) in data. Need both up and down days "
            "to train a real model. Saving a baseline model for now."
        )
        logger.warning(
            "Run the scraper daily to accumulate more data: "
            "python run_pipeline.py --collect"
        )

        # Train a dummy model that at least won't crash on predict
        # Add a fake row with the opposite class
        fake_row = X.iloc[[0]].copy()
        X_aug = pd.concat([X, fake_row], ignore_index=True)
        y_aug = pd.concat([y, pd.Series([1 - majority])], ignore_index=True)

        model = xgb.XGBClassifier(**config.XGB_PARAMS)
        model.fit(X_aug, y_aug, verbose=False)

        model.save_model(str(config.MODEL_PATH))
        logger.info(f"Baseline model saved to {config.MODEL_PATH}")

        meta = {
            "accuracy": 1.0,
            "f1": 0.0,
            "precision": 0.0,
            "recall": 0.0,
            "features": feature_cols,
            "feature_importance": {},
            "train_size": len(X),
            "test_size": 0,
            "note": f"Single-class baseline ({label}). Collect more data.",
        }
        meta_path = config.MODEL_DIR / "model_metadata.json"
        with open(meta_path, "w") as f:
            json.dump(meta, f, indent=2)

        return meta

    # -- Chronological split (adaptive to data size) -------------------
    if len(df) < 5:
        logger.warning(
            f"Small dataset ({len(df)} rows). Training on ALL data "
            "and evaluating on training set. Collect more data for proper validation."
        )
        X_train, X_test = X, X
        y_train, y_test = y, y
    else:
        split_idx = int(len(df) * config.TRAIN_TEST_SPLIT)
        split_idx = max(2, split_idx)
        X_train, X_test = X.iloc[:split_idx], X.iloc[split_idx:]
        y_train, y_test = y.iloc[:split_idx], y.iloc[split_idx:]

        # Check if test set has both classes
        if y_train.nunique() < 2:
            logger.warning("Training set has single class. Using all data.")
            X_train, X_test = X, X
            y_train, y_test = y, y

    logger.info(f"Train: {len(X_train)} | Test: {len(X_test)}")

    # -- Train XGBoost -------------------------------------------------
    model = xgb.XGBClassifier(**config.XGB_PARAMS)

    if not X_test.equals(X_train) and len(X_test) > 0:
        model.fit(
            X_train, y_train,
            eval_set=[(X_test, y_test)],
            verbose=False,
        )
    else:
        model.fit(X_train, y_train, verbose=False)

    # -- Evaluate ------------------------------------------------------
    y_pred = model.predict(X_test)

    acc = accuracy_score(y_test, y_pred)
    f1 = f1_score(y_test, y_pred, zero_division=0)
    prec = precision_score(y_test, y_pred, zero_division=0)
    rec = recall_score(y_test, y_pred, zero_division=0)
    cm = confusion_matrix(y_test, y_pred)

    logger.info("=" * 50)
    logger.info("MODEL PERFORMANCE")
    logger.info("=" * 50)
    logger.info(f"  Accuracy:  {acc:.4f}")
    logger.info(f"  F1 Score:  {f1:.4f}")
    logger.info(f"  Precision: {prec:.4f}")
    logger.info(f"  Recall:    {rec:.4f}")
    logger.info(f"\nConfusion Matrix:\n{cm}")
    logger.info(f"\n{classification_report(y_test, y_pred, zero_division=0)}")

    # -- Feature importance --------------------------------------------
    importance = dict(zip(feature_cols, model.feature_importances_))
    sorted_imp = sorted(importance.items(), key=lambda x: x[1], reverse=True)

    logger.info("\nTop 10 Features:")
    for feat, imp in sorted_imp[:10]:
        bar = "#" * int(imp * 50)
        logger.info(f"  {feat:25s} {imp:.4f} {bar}")

    # -- Save model ----------------------------------------------------
    model.save_model(str(config.MODEL_PATH))
    logger.info(f"\nModel saved to {config.MODEL_PATH}")

    meta = {
        "accuracy": round(acc, 4),
        "f1": round(f1, 4),
        "precision": round(prec, 4),
        "recall": round(rec, 4),
        "features": feature_cols,
        "feature_importance": {k: round(v, 4) for k, v in sorted_imp},
        "train_size": len(X_train),
        "test_size": len(X_test),
    }
    meta_path = config.MODEL_DIR / "model_metadata.json"
    with open(meta_path, "w") as f:
        json.dump(meta, f, indent=2)
    logger.info(f"Metadata saved to {meta_path}")

    return meta


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
    train()

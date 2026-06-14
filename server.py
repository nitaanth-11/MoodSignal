import sys
import os
import json
import logging
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional

import pandas as pd
from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Ensure project root is in path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import config
from model.predictor import predict

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger("moodsignal-server")

# Force UTF-8 encoding on stdout for Windows subprocesses
os.environ["PYTHONIOENCODING"] = "utf-8"

app = FastAPI(title="MoodSignal API", description="API server for MoodSignal Sentiment & Market Predictor")

# Setup CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins (Vite dev server)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class RunPipelineRequest(BaseModel):
    stage: str  # "collect", "analyze", "train", "all"
    no_finbert: Optional[bool] = True

# Global tracking of background task status
task_status = {
    "is_running": False,
    "current_stage": None,
    "last_run_success": None,
    "last_run_message": "Server idle"
}

def run_pipeline_subprocess(stage: str, no_finbert: bool):
    global task_status
    task_status["is_running"] = True
    task_status["current_stage"] = stage
    task_status["last_run_message"] = f"Running pipeline stage: {stage}..."
    
    cmd = [sys.executable, "run_pipeline.py"]
    if stage == "collect":
        cmd.append("--collect")
    elif stage == "analyze":
        cmd.append("--analyze")
    elif stage == "train":
        cmd.extend(["--features", "--train", "--predict"])
    elif stage == "all":
        # Runs the entire pipeline
        pass
    else:
        task_status["is_running"] = False
        task_status["last_run_success"] = False
        task_status["last_run_message"] = f"Unknown stage: {stage}"
        return

    if no_finbert:
        cmd.append("--no-finbert")

    logger.info(f"Running pipeline command: {' '.join(cmd)}")
    try:
        # Run process and capture output
        res = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=300 # 5 minutes max
        )
        if res.returncode == 0:
            task_status["last_run_success"] = True
            task_status["last_run_message"] = f"Successfully completed stage: {stage}"
            logger.info(task_status["last_run_message"])
        else:
            task_status["last_run_success"] = False
            task_status["last_run_message"] = f"Stage {stage} failed with code {res.returncode}. Error: {res.stderr[:200]}"
            logger.error(task_status["last_run_message"])
            logger.error(res.stderr)
    except Exception as e:
        task_status["last_run_success"] = False
        task_status["last_run_message"] = f"Error running pipeline: {str(e)}"
        logger.error(task_status["last_run_message"])
    finally:
        task_status["is_running"] = False
        task_status["current_stage"] = None


@app.get("/api/status")
def get_status():
    """Get the current running status of the pipeline background task."""
    return task_status


@app.post("/api/run")
def trigger_pipeline(req: RunPipelineRequest, background_tasks: BackgroundTasks):
    """Trigger a pipeline stage run as a background task."""
    if task_status["is_running"]:
        raise HTTPException(status_code=400, detail="A pipeline task is already running.")
        
    background_tasks.add_task(run_pipeline_subprocess, req.stage, req.no_finbert)
    return {"message": f"Triggered {req.stage} in background.", "status": "running"}


@app.get("/api/dashboard")
def get_dashboard_data():
    """Aggregates all data necessary for the React dashboard."""
    # 1. Fetch Latest Prediction
    prediction = {}
    try:
        if config.MODEL_PATH.exists() and config.FEATURES_CSV.exists():
            prediction = predict()
        else:
            prediction = {
                "error": "Model or features not found. Run Scraping & Retraining first."
            }
    except Exception as e:
        logger.error(f"Error generating prediction: {e}")
        prediction = {"error": f"Failed to load prediction: {str(e)}"}

    # 2. Get Model Metadata
    model_metadata = {}
    meta_path = config.MODEL_DIR / "model_metadata.json"
    try:
        if meta_path.exists():
            with open(meta_path, "r") as f:
                model_metadata = json.load(f)
    except Exception as e:
        logger.error(f"Error loading model metadata: {e}")

    # 3. Get Recent Scraped/Scored Posts Feed
    recent_posts = []
    try:
        posts_file = config.SCORED_POSTS_CSV if config.SCORED_POSTS_CSV.exists() else config.RAW_POSTS_CSV
        if posts_file.exists():
            df = pd.read_csv(posts_file)
            df = df.fillna("")
            # Reverse to get newest posts first
            latest_posts = df.iloc[::-1].head(50)
            recent_posts = latest_posts.to_dict(orient="records")
    except Exception as e:
        logger.error(f"Error loading posts: {e}")

    # 4. Get Historical Price + Mood Data for Charts
    chart_data = []
    try:
        if config.DAILY_MOOD_CSV.exists() and config.DJIA_PRICES_CSV.exists():
            mood_df = pd.read_csv(config.DAILY_MOOD_CSV)
            price_df = pd.read_csv(config.DJIA_PRICES_CSV)
            
            # Format dates to ensure exact matches
            mood_df["date"] = pd.to_datetime(mood_df["date"]).dt.strftime("%Y-%m-%d")
            price_df["date"] = pd.to_datetime(price_df["date"]).dt.strftime("%Y-%m-%d")
            
            # Merge on date
            merged = pd.merge(mood_df, price_df, on="date", how="inner").sort_values("date")
            merged = merged.fillna(0)
            
            # Add average/aggregate sentiment from scored posts if available
            if config.SCORED_POSTS_CSV.exists():
                posts_df = pd.read_csv(config.SCORED_POSTS_CSV)
                posts_df["timestamp"] = pd.to_datetime(posts_df["timestamp"], utc=True, errors="coerce")
                posts_df["date"] = posts_df["timestamp"].dt.strftime("%Y-%m-%d")
                
                daily_sent = posts_df.groupby("date")["sentiment_score"].mean().reset_index()
                daily_sent.columns = ["date", "social_sentiment"]
                
                merged = pd.merge(merged, daily_sent, on="date", how="left")
                merged["social_sentiment"] = merged["social_sentiment"].fillna(0)
            else:
                merged["social_sentiment"] = 0
                
            chart_data = merged.to_dict(orient="records")
    except Exception as e:
        logger.error(f"Error loading chart data: {e}")

    # 5. Extract Sentiment distribution for histogram
    sentiment_dist = []
    try:
        if config.SCORED_POSTS_CSV.exists():
            posts_df = pd.read_csv(config.SCORED_POSTS_CSV)
            scores = posts_df["sentiment_score"].dropna().tolist()
            # Bin into 10 groups from -1.0 to 1.0
            bins = [-1.0, -0.8, -0.6, -0.4, -0.2, 0.0, 0.2, 0.4, 0.6, 0.8, 1.0]
            counts, edge = pd.cut(scores, bins=bins, retbins=True).value_counts(sort=False)
            
            sentiment_dist = [
                {"bin": f"{round(bins[i], 1)} to {round(bins[i+1], 1)}", "count": int(count)}
                for i, count in enumerate(counts)
            ]
    except Exception as e:
        logger.error(f"Error generating sentiment distribution: {e}")

    return {
        "prediction": prediction,
        "metadata": model_metadata,
        "chart_data": chart_data,
        "posts": recent_posts,
        "sentiment_dist": sentiment_dist,
        "status": task_status
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="127.0.0.1", port=8000, reload=True)

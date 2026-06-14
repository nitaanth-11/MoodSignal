import React from "react";
import { Play, RefreshCw, Cpu, Database, Award, Loader2 } from "lucide-react";

export default function Header({ status, onRunStage }) {
  const isRunning = status?.is_running;
  const currentStage = status?.current_stage;
  const lastMsg = status?.last_run_message;

  return (
    <header className="glass-panel flex-between slide-up" style={{ padding: "16px 24px", marginBottom: "24px" }}>
      <div className="flex-align-center" style={{ gap: "16px" }}>
        <div 
          style={{
            background: "var(--grad-primary)",
            width: "48px",
            height: "48px",
            borderRadius: "12px",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            boxShadow: "0 0 15px rgba(0, 240, 255, 0.4)"
          }}
        >
          <Cpu size={24} color="#fff" />
        </div>
        <div>
          <h1 style={{ fontFamily: "var(--font-display)", fontSize: "24px", fontWeight: "800", letterSpacing: "-0.02em" }}>
            MoodSignal
          </h1>
          <p style={{ color: "var(--text-muted)", fontSize: "12px" }}>
            Stock Predictor & Social Sentiment Pipeline
          </p>
        </div>
      </div>

      <div className="flex-align-center" style={{ gap: "12px" }}>
        {/* Pipeline Controls */}
        <div style={{ display: "flex", gap: "8px" }}>
          <button 
            className="btn btn-secondary" 
            onClick={() => onRunStage("collect")}
            disabled={isRunning}
            title="Scrape data from StockTwits and Reddit"
          >
            <Database size={14} />
            <span>Scrape</span>
          </button>
          
          <button 
            className="btn btn-secondary" 
            onClick={() => onRunStage("analyze")}
            disabled={isRunning}
            title="Perform VADER and FinBERT sentiment scoring"
          >
            <Award size={14} />
            <span>Score</span>
          </button>

          <button 
            className="btn btn-secondary" 
            onClick={() => onRunStage("train")}
            disabled={isRunning}
            title="Engineer features, train XGBoost model, and make prediction"
          >
            <Cpu size={14} />
            <span>Retrain</span>
          </button>

          <button 
            className="btn btn-primary" 
            onClick={() => onRunStage("all")}
            disabled={isRunning}
            title="Run complete pipeline"
          >
            {isRunning ? (
              <Loader2 size={14} className="animate-spin" />
            ) : (
              <Play size={14} fill="#fff" />
            )}
            <span>{isRunning ? "Running..." : "Run All"}</span>
          </button>
        </div>

        {/* Task Status */}
        {isRunning && (
          <div 
            style={{ 
              display: "flex", 
              alignItems: "center", 
              gap: "8px", 
              background: "rgba(0, 240, 255, 0.1)", 
              border: "1px solid rgba(0, 240, 255, 0.2)",
              padding: "8px 12px", 
              borderRadius: "8px",
              fontSize: "12px",
              color: "var(--color-primary)"
            }}
          >
            <Loader2 size={14} className="animate-spin" />
            <span>Active: {currentStage}</span>
          </div>
        )}
      </div>
    </header>
  );
}

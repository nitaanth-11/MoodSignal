import React from "react";
import { TrendingUp, TrendingDown, HelpCircle, Info, Calendar } from "lucide-react";

export default function PredictionCard({ prediction, metadata }) {
  if (!prediction || prediction.error) {
    return (
      <div className="glass-panel slide-up flex-between" style={{ flexDirection: "column", height: "100%", justifyContent: "center", minHeight: "340px", gap: "16px" }}>
        <div style={{ background: "rgba(255, 190, 11, 0.1)", border: "1px solid rgba(255, 190, 11, 0.2)", borderRadius: "50%", width: "56px", height: "56px", display: "flex", alignItems: "center", justifyCenter: "center", display: "flex", justifyContent: "center" }}>
          <HelpCircle size={28} color="var(--color-neutral)" />
        </div>
        <div style={{ textAlign: "center" }}>
          <h3 style={{ fontFamily: "var(--font-display)", fontSize: "16px", marginBottom: "8px" }}>No Active Signal</h3>
          <p style={{ color: "var(--text-muted)", fontSize: "13px", lineHeight: "1.5" }}>
            {prediction?.error || "Run data collection and training to generate the first prediction signal."}
          </p>
        </div>
      </div>
    );
  }

  const isBullish = prediction.signal === "BULLISH";
  const confidence = prediction.confidence || 0.5;
  const isBaseline = metadata?.note?.includes("baseline") || !metadata?.test_size;

  // SVG circular progress details
  const radius = 42;
  const stroke = 6;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (confidence * circumference);

  return (
    <div 
      className="glass-panel slide-up" 
      style={{
        display: "flex",
        flexDirection: "column",
        justifyContent: "space-between",
        minHeight: "360px",
        background: isBullish ? "var(--grad-bullish)" : "var(--grad-bearish)",
        border: isBullish ? "1px solid rgba(0, 255, 136, 0.15)" : "1px solid rgba(255, 0, 85, 0.15)"
      }}
    >
      <div>
        <div className="flex-between" style={{ marginBottom: "20px" }}>
          <span style={{ fontSize: "12px", textTransform: "uppercase", letterSpacing: "0.1em", fontWeight: "700", color: "var(--text-muted)", fontFamily: "var(--font-display)" }}>
            Next-Day Signal
          </span>
          <div className="flex-align-center" style={{ color: "var(--text-dim)", gap: "4px" }}>
            <Calendar size={12} />
            <span style={{ fontSize: "11px" }}>{prediction.date}</span>
          </div>
        </div>

        {/* Prediction Value */}
        <div style={{ display: "flex", alignItems: "center", gap: "16px", marginBottom: "24px" }}>
          <div 
            style={{
              width: "56px",
              height: "56px",
              borderRadius: "14px",
              background: isBullish ? "rgba(0, 255, 136, 0.12)" : "rgba(255, 0, 85, 0.12)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              boxShadow: isBullish ? "0 0 20px rgba(0, 255, 136, 0.2)" : "0 0 20px rgba(255, 0, 85, 0.2)"
            }}
          >
            {isBullish ? (
              <TrendingUp size={28} color="var(--color-bullish)" />
            ) : (
              <TrendingDown size={28} color="var(--color-bearish)" />
            )}
          </div>
          <div>
            <h2 
              style={{
                fontFamily: "var(--font-display)",
                fontSize: "36px",
                fontWeight: "900",
                letterSpacing: "-0.03em",
                color: isBullish ? "var(--color-bullish)" : "var(--color-bearish)",
                textShadow: isBullish ? "0 0 15px rgba(0, 255, 136, 0.2)" : "0 0 15px rgba(255, 0, 85, 0.2)"
              }}
            >
              {prediction.signal}
            </h2>
            <p style={{ color: "var(--text-muted)", fontSize: "13px" }}>
              Target: Dow Jones (DJIA)
            </p>
          </div>
        </div>
      </div>

      {/* Confidence radial chart */}
      <div className="flex-between" style={{ background: "rgba(0,0,0,0.15)", borderRadius: "12px", padding: "16px", border: "1px solid rgba(255,255,255,0.02)" }}>
        <div style={{ flex: 1 }}>
          <div style={{ fontSize: "11px", color: "var(--text-muted)", textTransform: "uppercase", fontWeight: "600", marginBottom: "4px" }}>
            Model Confidence
          </div>
          <div style={{ color: "var(--text-main)", fontSize: "13px", fontWeight: "500" }}>
            XGBoost Probability
          </div>
        </div>
        
        <div style={{ position: "relative", width: "80px", height: "80px", display: "flex", alignItems: "center", justifyContent: "center" }}>
          <svg style={{ transform: "rotate(-90deg)", width: "80px", height: "80px" }}>
            <circle
              cx="40"
              cy="40"
              r={radius}
              stroke="rgba(255, 255, 255, 0.05)"
              strokeWidth={stroke}
              fill="transparent"
            />
            <circle
              cx="40"
              cy="40"
              r={radius}
              stroke={isBullish ? "var(--color-bullish)" : "var(--color-bearish)"}
              strokeWidth={stroke}
              fill="transparent"
              strokeDasharray={circumference}
              strokeDashoffset={offset}
              strokeLinecap="round"
              style={{ transition: "stroke-dashoffset 0.8s ease" }}
            />
          </svg>
          <div style={{ position: "absolute", fontFamily: "var(--font-display)", fontSize: "16px", fontWeight: "700" }}>
            {Math.round(confidence * 100)}%
          </div>
        </div>
      </div>

      {/* Baseline alert */}
      {isBaseline && (
        <div 
          style={{
            marginTop: "16px",
            display: "flex",
            gap: "8px",
            background: "rgba(255, 190, 11, 0.07)",
            border: "1px solid rgba(255, 190, 11, 0.15)",
            padding: "10px 12px",
            borderRadius: "8px",
            fontSize: "11px",
            color: "var(--color-neutral)",
            lineHeight: "1.4"
          }}
        >
          <Info size={14} style={{ flexShrink: 0, marginTop: "2px" }} />
          <span>
            <strong>Demo Baseline Mode</strong>: Limited overlapping history exists. Run the scraper daily to train a real prediction model.
          </span>
        </div>
      )}
    </div>
  );
}

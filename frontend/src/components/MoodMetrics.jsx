import React from "react";
import { Smile, AlertTriangle, Sun, Activity, Sparkles } from "lucide-react";

const DIMENSIONS_CONFIG = {
  calm: {
    label: "Calm",
    desc: "1 - Sentiment Volatility (high means steady consensus)",
    color: "#00f0ff",
    icon: Smile
  },
  fear: {
    label: "Fear",
    desc: "Strong negative posts & panic keywords",
    color: "#ff0055",
    icon: AlertTriangle
  },
  optimism: {
    label: "Optimism",
    desc: "Engagement-weighted positive scores",
    color: "#00ff88",
    icon: Sun
  },
  anxiety: {
    label: "Anxiety",
    desc: "Volatility + fear overlap (uncertain market)",
    color: "#ffbe0b",
    icon: Activity
  },
  happy: {
    label: "Happy",
    desc: "Rocket/moon mentions & strong positive peaks",
    color: "#bd00ff",
    icon: Sparkles
  }
};

export default function MoodMetrics({ mood }) {
  const activeMood = mood || { calm: 0, fear: 0, optimism: 0, anxiety: 0, happy: 0 };

  return (
    <div className="glass-panel slide-up" style={{ minHeight: "360px" }}>
      <h3 
        style={{ 
          fontFamily: "var(--font-display)", 
          fontSize: "16px", 
          fontWeight: "700", 
          marginBottom: "6px",
          textTransform: "uppercase",
          letterSpacing: "0.05em"
        }}
      >
        Social Mood Dimensions
      </h3>
      <p style={{ color: "var(--text-muted)", fontSize: "12px", marginBottom: "20px" }}>
        Today's dimensions aggregated from latest StockTwits and Reddit scraping
      </p>

      <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
        {Object.entries(DIMENSIONS_CONFIG).map(([key, cfg]) => {
          const val = activeMood[key] || 0;
          const Icon = cfg.icon;
          
          return (
            <div key={key} style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
              <div className="flex-between" style={{ fontSize: "13px" }}>
                <div className="flex-align-center" style={{ gap: "8px" }}>
                  <div 
                    style={{ 
                      width: "28px", 
                      height: "28px", 
                      borderRadius: "6px", 
                      background: `rgba(${parseInt(cfg.color.slice(1,3),16)}, ${parseInt(cfg.color.slice(3,5),16)}, ${parseInt(cfg.color.slice(5,7),16)}, 0.1)`,
                      display: "flex", 
                      alignItems: "center", 
                      justifyContent: "center",
                      border: `1px solid ${cfg.color}33`
                    }}
                  >
                    <Icon size={14} color={cfg.color} />
                  </div>
                  <div>
                    <span style={{ fontWeight: "600", color: key === "fear" ? "var(--color-bearish)" : "inherit" }}>
                      {cfg.label}
                    </span>
                    <span 
                      style={{ 
                        color: "var(--text-dim)", 
                        fontSize: "10px", 
                        marginLeft: "8px",
                        display: "inline-block"
                      }}
                      title={cfg.desc}
                    >
                      ({cfg.desc.slice(0, 32)}...)
                    </span>
                  </div>
                </div>
                <span style={{ fontFamily: "var(--font-display)", fontWeight: "700", color: cfg.color }}>
                  {Math.round(val * 100)}%
                </span>
              </div>
              
              {/* Progress track */}
              <div 
                style={{ 
                  height: "8px", 
                  width: "100%", 
                  background: "rgba(255, 255, 255, 0.03)", 
                  borderRadius: "4px",
                  overflow: "hidden",
                  border: "1px solid rgba(255, 255, 255, 0.02)"
                }}
              >
                <div 
                  style={{ 
                    height: "100%", 
                    width: `${val * 100}%`, 
                    background: cfg.color,
                    borderRadius: "4px",
                    boxShadow: `0 0 10px ${cfg.color}88`,
                    transition: "width 0.8s cubic-bezier(0.4, 0, 0.2, 1)"
                  }}
                />
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

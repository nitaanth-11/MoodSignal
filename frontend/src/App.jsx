import React, { useState, useEffect } from "react";
import { RefreshCw, BarChart, Percent, CheckSquare, Layers, HelpCircle, Loader2 } from "lucide-react";
import Header from "./components/Header";
import PredictionCard from "./components/PredictionCard";
import MoodMetrics from "./components/MoodMetrics";
import PriceChart from "./components/PriceChart";
import PostsFeed from "./components/PostsFeed";

// In production, the frontend is served by the same FastAPI server — use relative URLs.
// In development (Vite dev server on :5173), point to the local backend on :8000.
const API_BASE = import.meta.env.DEV
  ? "http://127.0.0.1:8000/api"
  : "/api";

export default function App() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [status, setStatus] = useState({ is_running: false, current_stage: null });
  const [refreshing, setRefreshing] = useState(false);

  const fetchData = async (showRefresh = false) => {
    if (showRefresh) setRefreshing(true);
    try {
      const res = await fetch(`${API_BASE}/dashboard`);
      if (!res.ok) throw new Error("Backend API not reachable");
      const json = await res.json();
      setData(json);
      setStatus(json.status);
      setError(null);
    } catch (err) {
      setError("Failed to connect to backend server. Make sure server.py is running on port 8000.");
      console.error(err);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  const checkStatus = async () => {
    try {
      const res = await fetch(`${API_BASE}/status`);
      if (!res.ok) return;
      const json = await res.json();
      setStatus(json);
      
      // If a task just finished running, reload dashboard data
      if (!json.is_running && status.is_running) {
        fetchData();
      }
    } catch (err) {
      console.error("Error checking status:", err);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  // Poll status frequently if a task is running
  useEffect(() => {
    let interval = null;
    if (status.is_running) {
      interval = setInterval(checkStatus, 1500);
    } else {
      // General keep-alive / slow poll every 20 seconds
      interval = setInterval(checkStatus, 20000);
    }
    return () => clearInterval(interval);
  }, [status.is_running]);

  const handleRunStage = async (stage) => {
    try {
      const res = await fetch(`${API_BASE}/run`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ stage, no_finbert: true })
      });
      if (!res.ok) {
        const errJson = await res.json();
        alert(errJson.detail || "Failed to trigger run.");
        return;
      }
      // Trigger local state update
      setStatus({ is_running: true, current_stage: stage });
    } catch (err) {
      alert("Error contacting API server to trigger pipeline.");
    }
  };

  if (loading) {
    return (
      <div 
        style={{ 
          height: "100vh", 
          display: "flex", 
          flexDirection: "column", 
          alignItems: "center", 
          justifyContent: "center",
          background: "var(--bg-color)",
          color: "var(--text-main)",
          gap: "16px"
        }}
      >
        <Loader2 size={36} className="animate-spin" color="var(--color-primary)" />
        <p style={{ fontFamily: "var(--font-display)", fontSize: "16px", fontWeight: "600", letterSpacing: "0.05em" }}>
          LOADING MOODSIGNAL...
        </p>
      </div>
    );
  }

  if (error) {
    return (
      <div 
        style={{ 
          height: "100vh", 
          display: "flex", 
          flexDirection: "column", 
          alignItems: "center", 
          justifyContent: "center",
          background: "var(--bg-color)",
          color: "var(--text-main)",
          padding: "24px",
          textAlign: "center",
          gap: "16px"
        }}
      >
        <div style={{ padding: "16px", background: "rgba(255, 0, 85, 0.1)", border: "1px solid rgba(255, 0, 85, 0.2)", borderRadius: "50%" }}>
          <HelpCircle size={36} color="var(--color-bearish)" />
        </div>
        <h2 style={{ fontFamily: "var(--font-display)", fontSize: "20px" }}>Connection Error</h2>
        <p style={{ color: "var(--text-muted)", maxWidth: "480px", fontSize: "14px", lineHeight: "1.5" }}>
          {error}
        </p>
        <button className="btn btn-primary" onClick={() => { setLoading(true); fetchData(); }} style={{ marginTop: "8px" }}>
          <RefreshCw size={14} />
          Try Again
        </button>
      </div>
    );
  }

  const prediction = data?.prediction;
  const metadata = data?.metadata;
  const chartData = data?.chart_data;
  const posts = data?.posts;

  return (
    <div className="app-container">
      {/* Header Panel */}
      <Header status={status} onRunStage={handleRunStage} />

      {/* Background Task Running Logs Overlay */}
      {status.is_running && (
        <div 
          className="slide-up"
          style={{
            background: "rgba(16, 22, 54, 0.9)",
            border: "1px solid rgba(0, 240, 255, 0.2)",
            borderRadius: "12px",
            padding: "16px 20px",
            marginBottom: "24px",
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            boxShadow: "0 0 20px rgba(0, 240, 255, 0.15)"
          }}
        >
          <div className="flex-align-center" style={{ gap: "12px" }}>
            <Loader2 className="animate-spin" size={18} color="var(--color-primary)" />
            <div>
              <div style={{ fontWeight: "700", fontSize: "13px" }}>Running: {status.current_stage?.toUpperCase()}</div>
              <div style={{ color: "var(--text-muted)", fontSize: "11px", marginTop: "2px" }}>
                {status.last_run_message}
              </div>
            </div>
          </div>
          <span style={{ fontSize: "10px", color: "var(--text-dim)", textTransform: "uppercase", letterSpacing: "0.05em" }}>
            Please wait...
          </span>
        </div>
      )}

      {/* Dashboard Grid */}
      <main className="grid-dashboard">
        {/* Left Column: Predictions & Mood Dimensions */}
        <div style={{ display: "flex", flexDirection: "column", gap: "24px" }}>
          {/* Circular Prediction Gauge */}
          <PredictionCard prediction={prediction} metadata={metadata} />
          
          {/* Mood Dimension Scores */}
          <MoodMetrics mood={prediction?.mood} />

          {/* Model Statistics Panel */}
          {metadata && Object.keys(metadata).length > 0 && (
            <div className="glass-panel slide-up" style={{ padding: "20px" }}>
              <h4 style={{ fontFamily: "var(--font-display)", fontSize: "13px", fontWeight: "700", textTransform: "uppercase", letterSpacing: "0.05em", marginBottom: "16px", color: "var(--text-muted)" }}>
                Model Training Stats
              </h4>
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px" }}>
                <div style={{ background: "rgba(255,255,255,0.015)", padding: "10px", borderRadius: "8px", border: "1px solid rgba(255,255,255,0.02)" }}>
                  <div style={{ fontSize: "10px", color: "var(--text-dim)" }}>TEST ACCURACY</div>
                  <div style={{ fontSize: "18px", fontWeight: "800", fontFamily: "var(--font-display)", color: "var(--color-primary)", marginTop: "2px" }}>
                    {metadata.accuracy ? `${(metadata.accuracy * 100).toFixed(1)}%` : "N/A"}
                  </div>
                </div>
                <div style={{ background: "rgba(255,255,255,0.015)", padding: "10px", borderRadius: "8px", border: "1px solid rgba(255,255,255,0.02)" }}>
                  <div style={{ fontSize: "10px", color: "var(--text-dim)" }}>F1 SCORE</div>
                  <div style={{ fontSize: "18px", fontWeight: "800", fontFamily: "var(--font-display)", color: "var(--color-secondary)", marginTop: "2px" }}>
                    {metadata.f1 ? `${(metadata.f1 * 100).toFixed(1)}%` : "N/A"}
                  </div>
                </div>
                <div style={{ background: "rgba(255,255,255,0.015)", padding: "10px", borderRadius: "8px", border: "1px solid rgba(255,255,255,0.02)" }}>
                  <div style={{ fontSize: "10px", color: "var(--text-dim)" }}>TRAINING ROWS</div>
                  <div style={{ fontSize: "16px", fontWeight: "700", fontFamily: "var(--font-display)", marginTop: "2px" }}>
                    {metadata.train_size || 0} days
                  </div>
                </div>
                <div style={{ background: "rgba(255,255,255,0.015)", padding: "10px", borderRadius: "8px", border: "1px solid rgba(255,255,255,0.02)" }}>
                  <div style={{ fontSize: "10px", color: "var(--text-dim)" }}>TEST ROWS</div>
                  <div style={{ fontSize: "16px", fontWeight: "700", fontFamily: "var(--font-display)", marginTop: "2px" }}>
                    {metadata.test_size || 0} days
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Right Column: Price Chart & Social Feed */}
        <div style={{ display: "flex", flexDirection: "column", gap: "24px" }}>
          {/* Main Price & Sentiment Line Chart */}
          <PriceChart data={chartData} />

          {/* Social Scraped Posts Feed */}
          <PostsFeed posts={posts} />
        </div>
      </main>
    </div>
  );
}

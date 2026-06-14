import React from "react";
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend
} from "recharts";
import { TrendingUp, BarChart2 } from "lucide-react";

export default function PriceChart({ data }) {
  if (!data || data.length === 0) {
    return (
      <div className="glass-panel slide-up flex-between" style={{ flexDirection: "column", height: "400px", justifyContent: "center", gap: "16px" }}>
        <div style={{ background: "rgba(255,255,255,0.03)", borderRadius: "50%", width: "56px", height: "56px", display: "flex", alignItems: "center", justifyContent: "center" }}>
          <BarChart2 size={24} color="var(--text-muted)" />
        </div>
        <p style={{ color: "var(--text-muted)", fontSize: "14px" }}>
          No historical price and sentiment overlap available. Run scraping & retraining first.
        </p>
      </div>
    );
  }

  // Format tooltip content
  const CustomTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
      return (
        <div 
          style={{
            background: "rgba(13, 18, 48, 0.95)",
            border: "1px solid var(--border-color)",
            padding: "12px 16px",
            borderRadius: "12px",
            boxShadow: "0 8px 32px 0 rgba(0, 0, 0, 0.4)",
            backdropFilter: "blur(4px)"
          }}
        >
          <p style={{ fontSize: "12px", fontWeight: "700", color: "var(--text-muted)", marginBottom: "8px" }}>
            Date: {label}
          </p>
          {payload.map((p, idx) => (
            <p key={idx} style={{ fontSize: "13px", fontWeight: "600", color: p.color, margin: "4px 0" }}>
              {p.name}: {p.name.includes("Price") ? `$${p.value.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}` : p.value.toFixed(3)}
            </p>
          ))}
        </div>
      );
    }
    return null;
  };

  return (
    <div className="glass-panel slide-up" style={{ minHeight: "420px" }}>
      <div className="flex-between" style={{ marginBottom: "20px" }}>
        <div>
          <h3 style={{ fontFamily: "var(--font-display)", fontSize: "16px", fontWeight: "700", display: "flex", alignItems: "center", gap: "8px" }}>
            <TrendingUp size={18} color="var(--color-primary)" />
            DJIA Price vs. Social Sentiment Overlay
          </h3>
          <p style={{ color: "var(--text-muted)", fontSize: "12px", marginTop: "2px" }}>
            Compares Daily Dow Jones industrial Close with aggregated social platform sentiment
          </p>
        </div>
      </div>

      <div style={{ width: "100%", height: "320px" }}>
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data} margin={{ top: 10, right: 5, left: -10, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.03)" vertical={false} />
            <XAxis 
              dataKey="date" 
              tick={{ fill: "var(--text-dim)", fontSize: 10 }}
              axisLine={{ stroke: "rgba(255,255,255,0.05)" }}
              tickLine={false}
            />
            <YAxis 
              yAxisId="left" 
              domain={["auto", "auto"]}
              tick={{ fill: "var(--text-dim)", fontSize: 10 }}
              axisLine={false}
              tickLine={false}
              tickFormatter={(v) => `$${Math.round(v).toLocaleString()}`}
            />
            <YAxis 
              yAxisId="right" 
              orientation="right"
              domain={[-1, 1]}
              tick={{ fill: "var(--text-dim)", fontSize: 10 }}
              axisLine={false}
              tickLine={false}
              tickFormatter={(v) => v.toFixed(1)}
            />
            <Tooltip content={<CustomTooltip />} />
            <Legend 
              wrapperStyle={{ fontSize: "12px", fontFamily: "var(--font-display)", paddingTop: "10px" }}
              iconSize={10}
              iconType="circle"
            />
            <Line
              yAxisId="left"
              type="monotone"
              dataKey="close"
              name="DJIA Price"
              stroke="var(--color-primary)"
              strokeWidth={3}
              dot={false}
              activeDot={{ r: 6, strokeWidth: 0, fill: "var(--color-primary)" }}
            />
            <Line
              yAxisId="right"
              type="monotone"
              dataKey="social_sentiment"
              name="Sentiment Score"
              stroke="var(--color-secondary)"
              strokeWidth={2}
              strokeDasharray="4 4"
              dot={false}
              activeDot={{ r: 4, strokeWidth: 0, fill: "var(--color-secondary)" }}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

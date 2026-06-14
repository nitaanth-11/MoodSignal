import React, { useState } from "react";
import { MessageSquare, Heart, Search, Filter, Share2 } from "lucide-react";

export default function PostsFeed({ posts }) {
  const [searchTerm, setSearchTerm] = useState("");
  const [sourceFilter, setSourceFilter] = useState("all");
  const [sentimentFilter, setSentimentFilter] = useState("all");

  if (!posts || posts.length === 0) {
    return (
      <div className="glass-panel slide-up flex-between" style={{ flexDirection: "column", height: "300px", justifyContent: "center", gap: "16px" }}>
        <MessageSquare size={32} color="var(--text-muted)" />
        <p style={{ color: "var(--text-muted)", fontSize: "14px" }}>
          No posts scraped yet. Click "Scrape" in the header to collect data.
        </p>
      </div>
    );
  }

  // Filter logic
  const filteredPosts = posts.filter((post) => {
    const text = (post.text || "").toLowerCase();
    const searchMatch = text.includes(searchTerm.toLowerCase());
    
    const source = post.source || "";
    const sourceMatch = sourceFilter === "all" || source === sourceFilter;
    
    // Scored score threshold
    const score = post.sentiment_score !== undefined ? post.sentiment_score : (post.vader_compound !== undefined ? post.vader_compound : 0);
    let sentimentType = "neutral";
    if (score > 0.1) sentimentType = "positive";
    else if (score < -0.1) sentimentType = "negative";

    const sentimentMatch = sentimentFilter === "all" || sentimentType === sentimentFilter;

    return searchMatch && sourceMatch && sentimentMatch;
  });

  const getSentimentBadge = (score) => {
    if (score > 0.1) {
      return <span className="badge badge-bullish">Pos (+{score.toFixed(2)})</span>;
    } else if (score < -0.1) {
      return <span className="badge badge-bearish">Neg ({score.toFixed(2)})</span>;
    } else {
      return <span className="badge badge-neutral">Neu ({score.toFixed(2)})</span>;
    }
  };

  return (
    <div className="glass-panel slide-up" style={{ minHeight: "450px" }}>
      <div className="flex-between" style={{ flexWrap: "wrap", gap: "16px", marginBottom: "20px" }}>
        <div>
          <h3 style={{ fontFamily: "var(--font-display)", fontSize: "16px", fontWeight: "700" }}>
            Social Sentiment Feed
          </h3>
          <p style={{ color: "var(--text-muted)", fontSize: "12px", marginTop: "2px" }}>
            Showing {filteredPosts.length} of {posts.length} latest posts
          </p>
        </div>

        {/* Filter Toolbar */}
        <div style={{ display: "flex", flexWrap: "wrap", gap: "10px", alignItems: "center" }}>
          {/* Search */}
          <div style={{ position: "relative", display: "flex", alignItems: "center" }}>
            <Search size={14} color="var(--text-dim)" style={{ position: "absolute", left: "10px" }} />
            <input
              type="text"
              placeholder="Search posts..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              style={{
                background: "rgba(255, 255, 255, 0.03)",
                border: "1px solid var(--border-color)",
                borderRadius: "8px",
                padding: "8px 12px 8px 30px",
                color: "var(--text-main)",
                fontSize: "12px",
                fontFamily: "var(--font-body)",
                width: "180px",
                outline: "none",
                transition: "border-color 0.2s"
              }}
              onFocus={(e) => e.target.style.borderColor = "var(--color-primary)"}
              onBlur={(e) => e.target.style.borderColor = "var(--border-color)"}
            />
          </div>

          {/* Source Filter */}
          <select
            value={sourceFilter}
            onChange={(e) => setSourceFilter(e.target.value)}
            style={{
              background: "rgba(255, 255, 255, 0.03)",
              border: "1px solid var(--border-color)",
              borderRadius: "8px",
              padding: "8px 12px",
              color: "var(--text-main)",
              fontSize: "12px",
              outline: "none",
              cursor: "pointer"
            }}
          >
            <option value="all" style={{ background: "#0a0e27" }}>All Sources</option>
            <option value="reddit" style={{ background: "#0a0e27" }}>Reddit</option>
            <option value="stocktwits" style={{ background: "#0a0e27" }}>StockTwits</option>
          </select>

          {/* Sentiment Filter */}
          <select
            value={sentimentFilter}
            onChange={(e) => setSentimentFilter(e.target.value)}
            style={{
              background: "rgba(255, 255, 255, 0.03)",
              border: "1px solid var(--border-color)",
              borderRadius: "8px",
              padding: "8px 12px",
              color: "var(--text-main)",
              fontSize: "12px",
              outline: "none",
              cursor: "pointer"
            }}
          >
            <option value="all" style={{ background: "#0a0e27" }}>All Sentiment</option>
            <option value="positive" style={{ background: "#0a0e27" }}>Positive</option>
            <option value="negative" style={{ background: "#0a0e27" }}>Negative</option>
            <option value="neutral" style={{ background: "#0a0e27" }}>Neutral</option>
          </select>
        </div>
      </div>

      {/* Feed list */}
      <div 
        style={{ 
          display: "flex", 
          flexDirection: "column", 
          gap: "12px", 
          maxHeight: "550px", 
          overflowY: "auto",
          paddingRight: "4px"
        }}
      >
        {filteredPosts.map((post, idx) => {
          const score = post.sentiment_score !== undefined ? post.sentiment_score : (post.vader_compound !== undefined ? post.vader_compound : 0);
          const isReddit = post.source === "reddit";
          
          return (
            <div 
              key={idx} 
              style={{
                background: "rgba(255, 255, 255, 0.015)",
                border: "1px solid rgba(255, 255, 255, 0.03)",
                borderRadius: "10px",
                padding: "16px",
                transition: "all 0.2s ease",
                display: "flex",
                flexDirection: "column",
                gap: "10px"
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.background = "rgba(255, 255, 255, 0.03)";
                e.currentTarget.style.borderColor = "rgba(255, 255, 255, 0.06)";
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.background = "rgba(255, 255, 255, 0.015)";
                e.currentTarget.style.borderColor = "rgba(255, 255, 255, 0.03)";
              }}
            >
              <div className="flex-between">
                <div className="flex-align-center" style={{ gap: "6px" }}>
                  <span 
                    style={{
                      fontSize: "10px",
                      fontWeight: "800",
                      background: isReddit ? "rgba(255, 87, 34, 0.15)" : "rgba(33, 150, 243, 0.15)",
                      color: isReddit ? "#ff5722" : "#2196f3",
                      border: isReddit ? "1px solid rgba(255, 87, 34, 0.2)" : "1px solid rgba(33, 150, 243, 0.2)",
                      padding: "2px 6px",
                      borderRadius: "4px",
                      textTransform: "uppercase",
                      letterSpacing: "0.05em",
                      fontFamily: "var(--font-display)"
                    }}
                  >
                    {post.source}
                  </span>
                  <span style={{ fontSize: "11px", fontWeight: "600", color: "var(--text-muted)" }}>
                    {isReddit ? `r/${post.subreddit}` : `$${post.subreddit}`}
                  </span>
                </div>
                
                {getSentimentBadge(score)}
              </div>

              {/* Text */}
              <p style={{ fontSize: "13px", lineHeight: "1.5", color: "var(--text-main)", overflowWrap: "break-word" }}>
                {post.text}
              </p>

              {/* Footer / Engagement */}
              <div className="flex-align-center" style={{ gap: "16px", color: "var(--text-dim)", fontSize: "11px" }}>
                <div className="flex-align-center" style={{ gap: "4px" }}>
                  <Heart size={12} />
                  <span>{post.score || 0}</span>
                </div>
                {isReddit && (
                  <div className="flex-align-center" style={{ gap: "4px" }}>
                    <MessageSquare size={12} />
                    <span>{post.num_comments || 0}</span>
                  </div>
                )}
                <div style={{ marginLeft: "auto", fontSize: "10px" }}>
                  {post.timestamp ? new Date(post.timestamp).toLocaleString(undefined, { dateStyle: "short", timeStyle: "short" }) : ""}
                </div>
              </div>
            </div>
          );
        })}

        {filteredPosts.length === 0 && (
          <div style={{ textAlign: "center", padding: "40px 0", color: "var(--text-dim)", fontSize: "13px" }}>
            No posts matches your search filters.
          </div>
        )}
      </div>
    </div>
  );
}

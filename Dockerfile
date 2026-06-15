# ============================================================
# MoodSignal — Production Dockerfile
# Multi-stage build: Node (frontend) → Python (backend + serve)
# ============================================================

# ---- Stage 1: Build React Frontend ----
FROM node:20-alpine AS frontend-builder

WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci --production=false
COPY frontend/ ./
RUN npm run build

# ---- Stage 2: Python Backend + Serve Static Frontend ----
FROM python:3.11-slim

# System deps for building wheels (numpy, pandas, etc.)
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc g++ && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend source
COPY config.py server.py run_pipeline.py ./
COPY collectors/ ./collectors/
COPY sentiment/ ./sentiment/
COPY mood/ ./mood/
COPY market/ ./market/
COPY model/ ./model/
# Copy built frontend from Stage 1
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist

# Create runtime directories
RUN mkdir -p data models

# Expose the API port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/status')" || exit 1

# Start server with gunicorn for production
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]

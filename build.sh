#!/usr/bin/env bash
# ============================================================
# MoodSignal — Render Build Script
# Installs Python deps + builds React frontend
# ============================================================

set -o errexit  # Exit on error

echo "╔══════════════════════════════════════════════╗"
echo "║   MoodSignal — Production Build              ║"
echo "╚══════════════════════════════════════════════╝"

# 1. Install Python dependencies
echo "→ Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# 2. Build React frontend
echo "→ Building React frontend..."
cd frontend
npm ci
npm run build
cd ..

# 3. Create runtime directories
echo "→ Creating runtime directories..."
mkdir -p data models

echo "✓ Build complete!"

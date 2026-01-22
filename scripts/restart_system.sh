#!/bin/bash

# Configuration
PROJECT_DIR="/Users/emimon/.gemini/antigravity/scratch/dashboard-ventas"
VENV_PYTHON="$PROJECT_DIR/venv/bin/python"
VENV_STREAMLIT="$PROJECT_DIR/venv/bin/streamlit"
LOG_DIR="$PROJECT_DIR/logs"

# Ensure log directory exists
mkdir -p "$LOG_DIR"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

echo "[$TIMESTAMP] Starting system restart..." >> "$LOG_DIR/restart.log"

# 1. Stop existing services
echo "Stopping services..."
pkill -f "src/api.py"
pkill -f "src/app.py"
sleep 2

# 2. Start API
echo "Starting API..."
nohup $VENV_PYTHON "$PROJECT_DIR/src/api.py" > "$LOG_DIR/api.log" 2>&1 &
API_PID=$!
echo "API started with PID $API_PID" >> "$LOG_DIR/restart.log"

# 3. Start Dashboard
echo "Starting Dashboard..."
nohup $VENV_STREAMLIT run "$PROJECT_DIR/src/app.py" > "$LOG_DIR/streamlit.log" 2>&1 &
DASH_PID=$!
echo "Dashboard started with PID $DASH_PID" >> "$LOG_DIR/restart.log"

echo "[$TIMESTAMP] Restart complete." >> "$LOG_DIR/restart.log"

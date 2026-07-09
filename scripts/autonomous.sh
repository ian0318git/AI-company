#!/usr/bin/env bash
# =============================================================================
# AI Team OS — Autonomous Mode Launcher
#
# Usage:
#   ./scripts/autonomous.sh              # Start autonomous mode (default 5-min loop)
#   ./scripts/autonomous.sh 10m          # Custom interval (e.g. 10m, 30m, 1h)
#   ./scripts/autonomous.sh once         # Run one cycle only
#   ./scripts/autonomous.sh stop         # Stop the autonomous loop
#
# What it does:
#   1. Starts the API server (if not running)
#   2. Starts the Dashboard (if not running)
#   3. Launches Claude Code in /loop mode with the autonomous prompt
#   4. System runs on its own — walk away
# =============================================================================

set -euo pipefail
cd "$(dirname "$0")/.."

INTERVAL="${1:-5m}"

# ── Ensure API server is running ──────────────────────────────────────────
if ! curl -s http://127.0.0.1:8765/health > /dev/null 2>&1; then
    echo "[Autonomous] Starting API server..."
    uv run aiteam serve --host 0.0.0.0 --port 8765 &
    sleep 3
fi

# ── Ensure Dashboard is running ───────────────────────────────────────────
if ! curl -s http://127.0.0.1:5173/ > /dev/null 2>&1; then
    echo "[Autonomous] Starting Dashboard..."
    cd dashboard && npm run dev -- --host 0.0.0.0 &
    cd ..
    sleep 2
fi

echo "=========================================="
echo "  AI Team OS — Autonomous Mode"
echo "=========================================="
echo "  API:       http://127.0.0.1:8765"
echo "  Dashboard: http://127.0.0.1:5173"
echo "  Interval:  $INTERVAL"
echo "=========================================="
echo ""
echo "System is running autonomously."
echo "Close this terminal or walk away."
echo "To stop: ./scripts/autonomous.sh stop"
echo ""

if [ "$INTERVAL" = "once" ]; then
    # Run one cycle only
    echo "[Autonomous] Running one cycle..."
    cat scripts/autonomous-prompt.md
    echo ""
    echo "[Autonomous] Cycle complete."
elif [ "$INTERVAL" = "stop" ]; then
    echo "[Autonomous] Stopping..."
    pkill -f "aiteam serve" 2>/dev/null || true
    pkill -f "vite" 2>/dev/null || true
    echo "[Autonomous] Stopped."
else
    # Convert interval to seconds
    case "$INTERVAL" in
        *m) SLEEP_SEC=$((${INTERVAL%m} * 60)) ;;
        *h) SLEEP_SEC=$((${INTERVAL%h} * 3600)) ;;
        *)  SLEEP_SEC=300 ;;
    esac

    echo "[Autonomous] Starting autonomous loop (every ${SLEEP_SEC}s)..."
    echo "[Autonomous] Press Ctrl+C to stop."

    CYCLE=0
    while true; do
        CYCLE=$((CYCLE + 1))
        TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
        echo ""
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo "[$TIMESTAMP] Cycle #$CYCLE"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

        claude --print --allowedTools "Bash(curl:*) Bash(git:*) Read Write Edit TaskCreate TaskUpdate Bash(python3:*)" -p "Autonomous cycle #$CYCLE. CRITICAL RULE: NEVER create new ideas. Only work on ideas that already exist in the inbox (created by the human user). If no tasks are todo, report 'Idle cycle' and skip. Scan ideas at http://127.0.0.1:8765/api/ideas/ — refine new ones that are in 'new' status, start pipelines for refined ones, execute up to 3 todo tasks from http://127.0.0.1:8765/api/tasks/, advance completed pipelines. Report 3-5 bullets of what you did." 2>&1

        echo "[$TIMESTAMP] Cycle #$CYCLE complete. Sleeping ${SLEEP_SEC}s..."
        sleep "$SLEEP_SEC"
    done
fi

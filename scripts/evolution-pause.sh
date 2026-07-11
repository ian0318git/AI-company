#!/usr/bin/env bash
# =============================================================================
# Evolution Pause/Resume Toggle
#
# Usage:
#   ./scripts/evolution-pause.sh           # Show current status
#   ./scripts/evolution-pause.sh pause     # Pause all self-evolution
#   ./scripts/evolution-pause.sh resume    # Resume self-evolution
# =============================================================================
set -euo pipefail

STATUS="${1:-status}"

case "$STATUS" in
    pause|off|stop|0)
        export AI_TEAM_EVOLUTION_PAUSED=true
        echo "export AI_TEAM_EVOLUTION_PAUSED=true" >> ~/.bashrc
        echo "⏸️  Self-evolution PAUSED."
        echo "    To resume: source <(./scripts/evolution-pause.sh resume)"
        echo "    Or:        export AI_TEAM_EVOLUTION_PAUSED=false"
        ;;
    resume|on|start|1)
        export AI_TEAM_EVOLUTION_PAUSED=false
        sed -i '/AI_TEAM_EVOLUTION_PAUSED/d' ~/.bashrc 2>/dev/null || true
        echo "▶️  Self-evolution RESUMED."
        ;;
    status|*)
        if [ "${AI_TEAM_EVOLUTION_PAUSED:-}" = "true" ] || [ "${AI_TEAM_EVOLUTION_PAUSED:-}" = "1" ]; then
            echo "⏸️  Self-evolution is PAUSED (AI_TEAM_EVOLUTION_PAUSED=true)"
        else
            echo "▶️  Self-evolution is ACTIVE"
        fi
        ;;
esac

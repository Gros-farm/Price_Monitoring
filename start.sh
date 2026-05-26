#!/bin/bash
set -e

PYTHON=/app/.venv/bin/python3
INTERVAL=7200  # 2 hours

agent_run() {
    echo "[agent] $(date -u +%Y-%m-%dT%H:%M:%SZ) starting..."
    $PYTHON scripts/agents/run.py --all \
        && echo "[agent] done" \
        || echo "[agent] failed (exit $?), keeping last cache"
}

# Background agent loop: run immediately, then every 2 hours
(
    while true; do
        agent_run
        sleep $INTERVAL
    done
) &

# Server in foreground — container lives while server is alive
exec node server.js

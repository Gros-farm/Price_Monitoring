#!/bin/zsh
set -u

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
PYTHON_BIN="${PRICE_MONITOR_PYTHON:-/private/tmp/price-monitor-venv/bin/python}"
BRANCH="${PRICE_MONITOR_BRANCH:-main}"

cd "$ROOT" || exit 1

echo "[$(date -u '+%Y-%m-%dT%H:%M:%SZ')] Starting Auchan scheduled update"

if [ ! -x "$PYTHON_BIN" ]; then
  echo "Python runtime not found or not executable: $PYTHON_BIN" >&2
  exit 1
fi

if ! git diff --cached --quiet; then
  echo "Skipped: there are staged changes. Please commit or unstage them before the scheduled agent runs." >&2
  git status --short
  exit 0
fi

if ! git diff --quiet -- . ":(exclude)data/auchan-products.json" ":(exclude)data/agent-status.json"; then
  echo "Skipped: there are local project changes outside agent data files." >&2
  git status --short
  exit 0
fi

git pull --ff-only origin "$BRANCH" || exit 1

"$PYTHON_BIN" scripts/agents/run.py --store auchan
agent_exit=$?

if ! git diff --quiet -- data/auchan-products.json data/agent-status.json; then
  git add data/auchan-products.json data/agent-status.json
  git commit -m "Update Auchan catalog [skip ci]"
  git push origin "$BRANCH"
else
  echo "No data changes to commit."
fi

echo "[$(date -u '+%Y-%m-%dT%H:%M:%SZ')] Finished Auchan scheduled update with agent exit code $agent_exit"
exit "$agent_exit"

#!/usr/bin/env bash
set -u

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
PYTHON_BIN="${PRICE_MONITOR_PYTHON:-${PYTHON:-python3}}"
BRANCH="${PRICE_MONITOR_BRANCH:-main}"
REPOSITORY="${GITHUB_REPOSITORY:-Gros-farm/Price_Monitoring}"

cd "$ROOT" || exit 1

echo "[$(date -u '+%Y-%m-%dT%H:%M:%SZ')] Starting remote Auchan update"

if [ "${REMOTE_AGENT_CLONE:-0}" = "1" ]; then
  if [ -z "${GITHUB_TOKEN:-}" ]; then
    echo "GITHUB_TOKEN is required when REMOTE_AGENT_CLONE=1." >&2
    exit 1
  fi

  WORK_DIR="${PRICE_MONITOR_WORKDIR:-/tmp/price-monitor-agent-repo}"
  rm -rf "$WORK_DIR"
  git clone --branch "$BRANCH" "https://x-access-token:${GITHUB_TOKEN}@github.com/${REPOSITORY}.git" "$WORK_DIR"
  cd "$WORK_DIR" || exit 1
fi

git config user.name "${GIT_AUTHOR_NAME:-grosfarm-agent}"
git config user.email "${GIT_AUTHOR_EMAIL:-agent@grosfarm.local}"

if ! git diff --cached --quiet; then
  echo "Skipped: there are staged changes." >&2
  git status --short
  exit 0
fi

if ! git diff --quiet -- . ":(exclude)data/auchan-products.json" ":(exclude)data/agent-status.json"; then
  echo "Skipped: there are project changes outside agent data files." >&2
  git status --short
  exit 0
fi

runner=()
if command -v xvfb-run >/dev/null 2>&1; then
  runner=(xvfb-run -a)
fi

"${runner[@]}" "$PYTHON_BIN" scripts/agents/run.py --store auchan
agent_exit=$?

if ! git diff --quiet -- data/auchan-products.json data/agent-status.json; then
  git add data/auchan-products.json data/agent-status.json
  git commit -m "Update Auchan catalog [skip ci]"
  if [ -n "${GITHUB_TOKEN:-}" ]; then
    git remote set-url origin "https://x-access-token:${GITHUB_TOKEN}@github.com/${REPOSITORY}.git"
  fi
  git push origin "$BRANCH"
else
  echo "No data changes to commit."
fi

echo "[$(date -u '+%Y-%m-%dT%H:%M:%SZ')] Finished remote Auchan update with agent exit code $agent_exit"
exit "$agent_exit"

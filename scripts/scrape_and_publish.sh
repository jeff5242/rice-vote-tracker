#!/usr/bin/env bash
# 抓取 → 重建儀表板 → push 到 GitHub Pages
set -uo pipefail

cd "$(dirname "$0")/.."
ROOT="$(pwd)"

LOG="$ROOT/logs/publish.log"
mkdir -p "$ROOT/logs"

ts() { date "+%Y-%m-%d %H:%M:%S"; }
log() { echo "[$(ts)] $*" >> "$LOG"; }

log "=== run start ==="

# 1. 抓取
"$ROOT/.venv/bin/python" "$ROOT/scripts/scrape.py" >> "$LOG" 2>&1
SCRAPE_RC=$?
if [ "$SCRAPE_RC" -ne 0 ]; then
    log "scrape failed rc=$SCRAPE_RC, skip publish"
    exit 0   # 不要因為單次失敗就停 launchd
fi

# 2. 重建 docs/index.html
"$ROOT/.venv/bin/python" "$ROOT/scripts/build_dashboard.py" >> "$LOG" 2>&1 || {
    log "build_dashboard failed"; exit 0;
}

# 3. git push（若有改動）
cd "$ROOT"
if [ -d .git ]; then
    git add -A docs/ data/ >> "$LOG" 2>&1
    if ! git diff --cached --quiet; then
        git -c user.name="vote-tracker auto" -c user.email="auto@local" \
            commit -m "auto: $(ts)" >> "$LOG" 2>&1 || true
        git push --quiet >> "$LOG" 2>&1 && log "pushed" || log "push failed (auth/network?)"
    else
        log "no changes to commit"
    fi
else
    log "not a git repo, skip push"
fi

log "=== run end ==="

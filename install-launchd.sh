#!/usr/bin/env bash
# 把排程任務裝進 LaunchAgents（每 30 分鐘跑一次抓取）
set -euo pipefail
cd "$(dirname "$0")"

PLIST_SRC="$(pwd)/com.jef.vote-tracker.plist"
PLIST_DST="$HOME/Library/LaunchAgents/com.jef.vote-tracker.plist"

mkdir -p "$HOME/Library/LaunchAgents"
# 若已存在，先卸載再覆寫
if [ -f "$PLIST_DST" ]; then
    launchctl unload "$PLIST_DST" 2>/dev/null || true
fi
cp "$PLIST_SRC" "$PLIST_DST"
launchctl load "$PLIST_DST"

echo "[OK] 已啟動 com.jef.vote-tracker (每 30 分鐘自動抓取)"
echo "查看狀態: launchctl list | grep vote-tracker"
echo "查看 log:  tail -f logs/scraper.out.log"
echo "停用:     launchctl unload $PLIST_DST"

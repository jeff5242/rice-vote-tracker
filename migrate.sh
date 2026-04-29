#!/usr/bin/env bash
# 一鍵移轉到新 Mac：停舊排程（若有）→ 取最新程式碼 → 建 venv → 載入 launchd → 跑一次測試
set -uo pipefail

TARGET="$HOME/CodeRepository/vote-auto-crawl/vote-tracker"
REPO="git@github.com:jeff5242/rice-vote-tracker.git"
PLIST="$HOME/Library/LaunchAgents/com.jef.vote-tracker.plist"

echo "=== Rice Vote Tracker 移轉腳本 ==="
echo

# 1. 停舊排程（若存在）
echo "[1/5] 檢查並停用既有排程..."
if [ -f "$PLIST" ]; then
    launchctl unload "$PLIST" 2>/dev/null && echo "  已 unload 舊 launchd" || echo "  (舊 launchd 已不在運行)"
else
    echo "  (沒有既有 plist)"
fi

# 2. 取得程式碼
echo "[2/5] 取得最新程式碼..."
mkdir -p "$(dirname "$TARGET")"
if [ -d "$TARGET/.git" ]; then
    cd "$TARGET"
    REMOTE_URL=$(git remote get-url origin 2>/dev/null || echo "")
    if echo "$REMOTE_URL" | grep -q rice-vote-tracker; then
        echo "  既有 repo，git pull..."
        git fetch origin
        git reset --hard origin/main
    else
        echo "  既有資料夾不是 rice-vote-tracker，備份後 clone..."
        cd ..
        mv vote-tracker "vote-tracker.bak.$(date +%Y%m%d-%H%M%S)"
        git clone "$REPO" vote-tracker
        cd vote-tracker
    fi
elif [ -d "$TARGET" ]; then
    echo "  既有資料夾不是 git repo，備份後 clone..."
    mv "$TARGET" "${TARGET}.bak.$(date +%Y%m%d-%H%M%S)"
    git clone "$REPO" "$TARGET"
    cd "$TARGET"
else
    echo "  全新 clone..."
    git clone "$REPO" "$TARGET"
    cd "$TARGET"
fi
echo "  程式碼位置：$(pwd)"

# 3. venv
echo "[3/5] 建立 / 確認 venv..."
if ! command -v python3 >/dev/null 2>&1; then
    echo "  錯誤：找不到 python3，請先安裝。" >&2
    exit 1
fi
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
    echo "  建立 .venv"
fi
.venv/bin/pip install --quiet --upgrade pip 2>&1 | tail -1 || true
mkdir -p data logs reports

# 4. launchd
echo "[4/5] 安裝 launchd..."
bash install-launchd.sh

# 5. 立即跑一次驗證
echo "[5/5] 跑一次抓取測試..."
sleep 3
if .venv/bin/python scripts/scrape.py; then
    echo "  ✅ 抓取成功"
else
    echo "  ⚠️  抓取失敗，請檢查 logs/"
fi

echo
echo "=== 移轉完成 ==="
echo
echo "公開網址 :  https://jeff5242.github.io/rice-vote-tracker/"
echo "本機資料 :  $TARGET/data/vote-history.jsonl"
echo "排程 log :  $TARGET/logs/publish.log"
echo
echo "確認新機運作正常後，到舊機執行："
echo "  launchctl unload ~/Library/LaunchAgents/com.jef.vote-tracker.plist"

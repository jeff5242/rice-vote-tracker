#!/usr/bin/env bash
# 一次性安裝：建立 venv、安裝 Playwright、下載 Chromium
set -euo pipefail

cd "$(dirname "$0")"

echo "[1/4] 檢查 Python 3..."
if ! command -v python3 >/dev/null 2>&1; then
    echo "錯誤：找不到 python3。請先安裝（建議 brew install python@3.12）。" >&2
    exit 1
fi
python3 --version

echo "[2/4] 建立 venv..."
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
fi
# shellcheck disable=SC1091
source .venv/bin/activate

echo "[3/4] 安裝 Playwright..."
pip install --quiet --upgrade pip
pip install --quiet playwright

echo "[4/4] 下載 Chromium..."
python -m playwright install chromium

mkdir -p data logs

echo
echo "[OK] 安裝完成。執行一次抓取測試："
echo "    .venv/bin/python scripts/scrape.py"

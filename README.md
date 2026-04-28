# Rice Vote Tracker

2026 精饌米獎 網路人氣票選 - 票數監測與分析

## 功能

- 每 30 分鐘抓一次 [官網](https://taiwanriceaward2026.com.tw/) 的票數（直接解析 `data-name` / `data-votes`）
- 累積成時間序列 `data/vote-history.jsonl`
- 自動產生靜態儀表板 `docs/index.html`，推到 GitHub Pages 公開分享
- 可產出 Markdown 分析報告（`scripts/analyze.py`）

## 追蹤對象

- 大橋頂級CAS越光米（米屋智農股份有限公司）
- 金農職人臺灣越光米（宇進實業股份有限公司）

可在 `scripts/scrape.py` 的 `TARGETS` 修改。

## 快速開始

```bash
# 1. 安裝相依（一次性）
bash setup.sh

# 2. 手動跑一次抓取
.venv/bin/python scripts/scrape.py

# 3. 重建儀表板
.venv/bin/python scripts/build_dashboard.py

# 4. 啟動每 30 分鐘自動排程
bash install-launchd.sh
```

## 結構

```
vote-tracker/
├── scripts/
│   ├── scrape.py              # 抓票數，append 到 vote-history.jsonl
│   ├── build_dashboard.py     # 從 jsonl 產出 docs/index.html
│   ├── analyze.py             # 產 Markdown 分析報告
│   └── scrape_and_publish.sh  # 抓取 → 重建 → git push（launchd 跑）
├── data/
│   └── vote-history.jsonl     # 時間序列原始資料
├── docs/
│   ├── index.html             # GitHub Pages 公開儀表板
│   └── data.json              # 公開原始資料
├── reports/                   # 24 小時分析報告
├── com.jef.vote-tracker.plist # launchd 排程設定
└── install-launchd.sh         # 安裝排程
```

## 移除排程

```bash
launchctl unload ~/Library/LaunchAgents/com.jef.vote-tracker.plist
```

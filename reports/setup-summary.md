# 票數監測系統建置報告

**建置時間：** 2026-04-28 21:56 (UTC+8)
**監測對象：** 大橋頂級CAS越光米、金農職人臺灣越光米
**監測週期：** 4/28 21:36 ~ 4/30 23:59（投票結束）

## 公開網址

**https://jeff5242.github.io/rice-vote-tracker/**

別人開這個連結就能看到即時票數曲線、深夜異常標記、最近 12 筆紀錄等視覺化內容。每 30 分鐘自動更新一次。

## 系統架構

```
launchd (每 30 分鐘)
    ↓
scrape_and_publish.sh
    ├── scripts/scrape.py
    │     直接 HTTP fetch 官網 → 解析 data-name/data-votes
    │     寫入 data/vote-history.jsonl（append）
    ├── scripts/build_dashboard.py
    │     讀取 jsonl → 重建 docs/index.html（資料嵌入）
    └── git add/commit/push
          推到 https://github.com/jeff5242/rice-vote-tracker
          → GitHub Pages 自動 rebuild → 1 分鐘後對外可見
```

## 已完成項目

| 項目 | 狀態 |
| --- | --- |
| Python + venv 環境 | ✅ |
| 抓取腳本（純 HTTP，無需 Playwright 渲染） | ✅ |
| 第一次抓取驗證（20 位候選人完整抓到） | ✅ |
| launchd 排程（每 30 分鐘） | ✅ |
| Cowork 本機儀表板 Artifact | ✅ 僅你看得到 |
| GitHub repo + Pages | ✅ jeff5242/rice-vote-tracker（public） |
| 靜態儀表板產生器 | ✅ |
| 自動 git push 整合 | ✅ |
| 端到端 pipeline 驗證 | ✅ 5 筆紀錄上傳成功 |

## 起始基準（2026-04-28 21:36）

| 候選人 | 起始票數 |
| --- | ---: |
| 大橋頂級CAS越光米 | 8,726 |
| 金農職人臺灣越光米 | 8,530 |

## 接下來會自動發生

1. launchd 每 30 分鐘觸發一次（下次約 22:20）
2. 每次抓取後自動 commit + push
3. GitHub Pages 自動 rebuild
4. 連結頁面數據會自動更新

## 24 小時後（4/29 21:56）

執行下列指令產出完整 Markdown 分析報告：

```bash
cd /Users/jef/CodeRepository/vote-auto-crawl/vote-tracker
.venv/bin/python scripts/analyze.py --hours 24
```

報告會輸出到 `reports/vote-report-YYYYMMDD-HHMM.md`，包含：

- 票數總覽
- 各時段（24 個小時）平均增量
- 深夜（00-06）vs 白天（06-24）增量比較與倍數
- ASCII 走勢圖
- 異常時段標記（z-score ≥ 2 標 **異常高**）

## 監測注意事項

1. **Mac 不能完全關機或睡眠太久**——launchd 在睡眠時不會觸發。建議將電源設為「永不睡眠」或保持開機。
2. **網路要通**——若官網或 GitHub 暫時不可達會 log 失敗但不會中斷排程。
3. **隱私**——Repo 是 public，但網址沒有列在 GitHub 搜尋首頁，連結沒給對方就不會被找到。
4. **截止日 4/30 23:59 之後**——可手動執行 `launchctl unload ~/Library/LaunchAgents/com.jef.vote-tracker.plist` 停止。

## 檔案位置

- 工作目錄：`/Users/jef/CodeRepository/vote-auto-crawl/vote-tracker`
- 抓取 log：`logs/publish.log`
- 原始資料：`data/vote-history.jsonl`（公開於 https://jeff5242.github.io/rice-vote-tracker/data.json）

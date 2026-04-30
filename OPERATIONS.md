# Operations 維運手冊

> 任何時候要查「程式怎麼跑、怎麼修、怎麼改」，先看這份。

## 系統架構速查

```
launchd (每 5 分鐘觸發)
    ↓ 執行 ProgramArguments
scripts/scrape_and_publish.sh
    ├── scripts/scrape.py       直接 HTTP fetch 官網 → append 到 data/vote-history.jsonl
    ├── scripts/build_dashboard.py  讀 jsonl → 產出 docs/index.html
    └── git add → commit → push  → GitHub Pages 自動 rebuild
```

## 排程設定在哪裡

| 內容 | 位置 |
| --- | --- |
| 排程間隔 (秒) | `com.jef.vote-tracker.plist` 的 `<key>StartInterval</key><integer>300</integer>` |
| 安裝後的 plist | `~/Library/LaunchAgents/com.jef.vote-tracker.plist` |
| 執行的腳本 | plist 內 `ProgramArguments` 指向 `scripts/scrape_and_publish.sh` |
| 工作目錄 | plist 內 `WorkingDirectory` 指向 `~/CodeRepository/vote-auto-crawl/vote-tracker` |
| 標準輸出 log | `logs/scraper.out.log` |
| 錯誤 log | `logs/scraper.err.log` |
| 詳細執行 log | `logs/publish.log` |

## 確認排程是否運行中

```bash
launchctl list | grep vote-tracker
```

- 顯示 `<PID>  0  com.jef.vote-tracker` → 正常運行（PID 是數字）
- 顯示 `-  0  com.jef.vote-tracker` → 已載入但目前沒在跑（正常，等下次 trigger）
- 沒有任何輸出 → **沒載入**，需要 `bash install-launchd.sh`

## 確認最近抓取是否成功

```bash
cd ~/CodeRepository/vote-auto-crawl/vote-tracker
tail -10 logs/publish.log
```

最近一筆若有 `pushed` 字樣表示成功推到 GitHub。

或看 GitHub Pages 上的「最後更新」：
<https://jeff5242.github.io/rice-vote-tracker/>

## 常見維運操作

### 啟動 / 重啟 / 停止排程

```bash
cd ~/CodeRepository/vote-auto-crawl/vote-tracker

# 啟動（首次或被 unload 後）
bash install-launchd.sh

# 停止
launchctl unload ~/Library/LaunchAgents/com.jef.vote-tracker.plist

# 重啟（修改 plist 後必做）
launchctl unload ~/Library/LaunchAgents/com.jef.vote-tracker.plist 2>/dev/null
bash install-launchd.sh
```

### 改變抓取頻率

編輯 `com.jef.vote-tracker.plist`：

```xml
<key>StartInterval</key>
<integer>300</integer>   <!-- 秒；300=5min, 1800=30min, 600=10min -->
```

改完後 → `bash install-launchd.sh` 重新載入。

### 立即跑一次（測試）

```bash
cd ~/CodeRepository/vote-auto-crawl/vote-tracker
bash scripts/scrape_and_publish.sh
tail -5 logs/publish.log
```

### 看最新一筆票數

```bash
tail -1 ~/CodeRepository/vote-auto-crawl/vote-tracker/data/vote-history.jsonl | python3 -m json.tool
```

### 換追蹤對象

編輯 `scripts/scrape.py` 的 `TARGETS` 陣列：

```python
TARGETS = [
    "大橋頂級CAS越光米",
    "金農職人臺灣越光米",
]
```

完整候選人名稱在官網 HTML 的 `data-name=""` 屬性裡，或執行一次抓取後看 `data/vote-history.jsonl` 內 `all_candidates` 列表。

修改後 push 到 GitHub，下次 cron 自動套用。

## 移轉 / 重灌（在新 Mac 上）

```bash
bash <(curl -fsSL https://raw.githubusercontent.com/jeff5242/rice-vote-tracker/main/migrate.sh)
```

`migrate.sh` 會自動：
1. 停掉既有排程（若存在）
2. 從 GitHub 拉最新程式碼到 `~/CodeRepository/vote-auto-crawl/vote-tracker`
3. 建 venv（純 stdlib，不需額外套件）
4. **呼叫 `install-launchd.sh` 載入 5 分鐘排程**
5. 立即跑一次驗證

跑完後一定要看到 `[OK] 已啟動 com.jef.vote-tracker` 字樣，那就代表 5 分鐘排程已啟用。

## 故障排除

### `migrate.sh` 跑完但沒在自動抓

```bash
# 確認 plist 是否載入
launchctl list | grep vote-tracker

# 沒載入 → 手動載入
cd ~/CodeRepository/vote-auto-crawl/vote-tracker
bash install-launchd.sh

# 立即測試
bash scripts/scrape_and_publish.sh
tail -10 logs/publish.log
```

### 抓到了但沒 push 到 GitHub

```bash
# 看是不是 SSH 認證問題
cd ~/CodeRepository/vote-auto-crawl/vote-tracker
git push 2>&1 | head -5

# 如果是 Permission denied → SSH key 沒加到 GitHub
ssh -T git@github.com
```

### 多台機器同時跑會打架嗎

會。兩台同時推 git 會有 reject + retry，雖然不會壞但浪費資源。建議只在一台跑，另一台 unload。

## 公開頁面

| URL | 用途 |
| --- | --- |
| <https://jeff5242.github.io/rice-vote-tracker/> | 即時票數儀表板 |
| <https://jeff5242.github.io/rice-vote-tracker/vote.html?openExternalBrowser=1> | 拜票落地頁（給朋友） |
| <https://jeff5242.github.io/rice-vote-tracker/data.json> | 原始資料 JSON |

## 相關檔案速查

| 檔案 | 角色 |
| --- | --- |
| `scripts/scrape.py` | 主爬蟲（純 stdlib urllib） |
| `scripts/build_dashboard.py` | 從 jsonl 產靜態儀表板 |
| `scripts/scrape_and_publish.sh` | launchd 觸發的 wrapper |
| `scripts/analyze.py` | 產 24 小時 Markdown 報告 |
| `scripts/capture_card.py` | 重新擷取拜票落地頁的卡片圖 |
| `install-launchd.sh` | 安裝排程 |
| `migrate.sh` | 跨機移轉 |
| `setup.sh` | 首次安裝（含 Playwright，目前其實不必要） |
| `com.jef.vote-tracker.plist` | launchd 設定 |

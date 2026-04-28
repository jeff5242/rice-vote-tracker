#!/usr/bin/env python3
"""
2026 精饌米獎 網路人氣票選 - 票數抓取器
直接 HTTP 抓首頁 HTML，解析每張卡片的 data-name / data-votes 屬性。
每次執行 append 一筆紀錄到 data/vote-history.jsonl。
"""
from __future__ import annotations

import json
import re
import sys
import traceback
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

URL = "https://taiwanriceaward2026.com.tw/"

# 追蹤目標：用 data-name 完全比對的關鍵字
TARGETS = [
    "大橋頂級CAS越光米",
    "金農職人臺灣越光米",
]

PROJECT_DIR = Path(__file__).resolve().parent.parent
DATA_FILE = PROJECT_DIR / "data" / "vote-history.jsonl"
SNAPSHOT_FILE = PROJECT_DIR / "data" / "last-snapshot.json"

TPE = timezone(timedelta(hours=8))

CARD_PATTERN = re.compile(
    r'data-name="(?P<name>[^"]+)"'
    r'(?:[^>]*?data-desc="(?P<desc>[^"]*)")?'
    r'[^>]*?data-votes="(?P<votes>\d+)"',
    re.DOTALL,
)
GROUP_PATTERN = re.compile(
    r'class="group-section\s+group-(?P<gcode>[a-z-]+)\s+panel-section[^"]*"'
    r'(?P<body>[\s\S]*?)(?=class="group-section|$)',
)


def now_tpe_iso() -> str:
    return datetime.now(TPE).isoformat(timespec="seconds")


def fetch_html(url: str = URL, timeout: int = 20) -> str:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            "Accept-Language": "zh-TW,zh;q=0.9,en;q=0.8",
        },
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read().decode("utf-8", errors="replace")


def parse_cards(html: str) -> list[dict]:
    """解析所有候選人卡片，附上分組（香米 / 非香米）。"""
    # 先嘗試把每個 group section 切出來，標記分組
    cards: list[dict] = []
    seen_names: set[str] = set()

    for gm in re.finditer(
        r'group-(?P<gcode>xiang|non-xiang)\s+panel-section[^>]*>(?P<body>[\s\S]*?)</section>',
        html,
    ):
        group = "香米組" if gm.group("gcode") == "xiang" else "非香米組"
        for m in CARD_PATTERN.finditer(gm.group("body")):
            name = m.group("name").strip()
            if name in seen_names:
                continue
            seen_names.add(name)
            cards.append({
                "name": name,
                "votes": int(m.group("votes")),
                "group": group,
            })

    # Fallback：若分組切不到，整頁掃過一次
    if not cards:
        for m in CARD_PATTERN.finditer(html):
            name = m.group("name").strip()
            if name in seen_names:
                continue
            seen_names.add(name)
            cards.append({
                "name": name,
                "votes": int(m.group("votes")),
                "group": None,
            })

    return cards


def extract_targets(cards: list[dict]) -> dict[str, int | None]:
    out: dict[str, int | None] = {n: None for n in TARGETS}
    for c in cards:
        for t in TARGETS:
            if c["name"] == t or t in c["name"]:
                out[t] = c["votes"]
    return out


def append_record(record: dict) -> None:
    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    with DATA_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
    SNAPSHOT_FILE.write_text(
        json.dumps(record, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def main() -> int:
    started = now_tpe_iso()
    try:
        html = fetch_html()
        cards = parse_cards(html)
        targets = extract_targets(cards)
        record = {
            "timestamp": started,
            "url": URL,
            "targets": targets,
            "all_candidates": cards,
            "n_candidates": len(cards),
            "ok": all(v is not None for v in targets.values()) and len(cards) >= 10,
        }
        append_record(record)
        print(json.dumps(
            {
                "timestamp": record["timestamp"],
                "targets": record["targets"],
                "n_candidates": record["n_candidates"],
                "ok": record["ok"],
            },
            ensure_ascii=False,
        ))
        return 0 if record["ok"] else 2
    except Exception as e:
        record = {
            "timestamp": started,
            "error": str(e),
            "trace": traceback.format_exc(),
            "ok": False,
        }
        append_record(record)
        print(json.dumps(
            {"timestamp": started, "error": str(e), "ok": False},
            ensure_ascii=False,
        ), file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())

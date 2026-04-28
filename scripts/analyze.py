#!/usr/bin/env python3
"""
從 vote-history.jsonl 產出 24 小時 Markdown 分析報告。
用法：
    .venv/bin/python scripts/analyze.py [--hours 24] [--out report.md]
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from statistics import mean, pstdev

PROJECT_DIR = Path(__file__).resolve().parent.parent
DATA_FILE = PROJECT_DIR / "data" / "vote-history.jsonl"
DEFAULT_OUT = PROJECT_DIR / "reports"

TPE = timezone(timedelta(hours=8))


def load_records(path: Path) -> list[dict]:
    if not path.exists():
        return []
    out = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return out


def to_dt(ts: str) -> datetime:
    return datetime.fromisoformat(ts)


def deltas_per_target(records: list[dict]) -> dict[str, list[tuple[datetime, int, int]]]:
    """為每個目標，產出 [(timestamp, votes, delta_since_prev), ...]"""
    out: dict[str, list[tuple[datetime, int, int]]] = {}
    by_target: dict[str, list[tuple[datetime, int]]] = {}
    for r in records:
        if not r.get("ok"):
            continue
        ts = to_dt(r["timestamp"])
        for name, v in (r.get("targets") or {}).items():
            if v is None:
                continue
            by_target.setdefault(name, []).append((ts, v))
    for name, series in by_target.items():
        series.sort(key=lambda x: x[0])
        rows = []
        prev = None
        for ts, v in series:
            d = 0 if prev is None else v - prev
            rows.append((ts, v, d))
            prev = v
        out[name] = rows
    return out


def hour_bucket(dt: datetime) -> int:
    return dt.hour


def is_overnight(hour: int) -> bool:
    """定義深夜時段：00:00-06:00"""
    return 0 <= hour <= 5


def render_ascii_chart(values: list[int], width: int = 50, height: int = 10) -> str:
    """簡易 ASCII 走勢圖。"""
    if not values:
        return "(no data)"
    lo, hi = min(values), max(values)
    span = max(1, hi - lo)
    rows = [[" "] * width for _ in range(height)]
    n = len(values)
    for i in range(width):
        idx = int(i * (n - 1) / max(1, width - 1)) if n > 1 else 0
        v = values[idx]
        y = height - 1 - int((v - lo) / span * (height - 1))
        rows[y][i] = "·"
    return "\n".join("    " + "".join(r) for r in rows)


def write_report(records: list[dict], hours: int, out_path: Path) -> Path:
    cutoff = datetime.now(TPE) - timedelta(hours=hours)
    in_window = [r for r in records if r.get("ok") and to_dt(r["timestamp"]) >= cutoff]

    lines: list[str] = []
    now_str = datetime.now(TPE).strftime("%Y-%m-%d %H:%M:%S %z")
    lines.append(f"# 2026 精饌米獎 投票追蹤報告")
    lines.append("")
    lines.append(f"- 報告產生時間：{now_str}")
    lines.append(f"- 分析時間範圍：過去 {hours} 小時")
    lines.append(f"- 有效資料點數：{len(in_window)}")
    lines.append(f"- 來源：{records[0]['url'] if records else 'N/A'}")
    lines.append("")

    if not in_window:
        lines.append("> 資料不足，請等更多抓取週期完成後再產出報告。")
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text("\n".join(lines), encoding="utf-8")
        return out_path

    series = deltas_per_target(in_window)

    # 概覽
    lines.append("## 票數總覽")
    lines.append("")
    lines.append("| 候選人 | 起始票數 | 最新票數 | 期間增加 | 平均每小時 |")
    lines.append("| --- | ---: | ---: | ---: | ---: |")
    for name, rows in series.items():
        if not rows:
            continue
        first = rows[0][1]
        last = rows[-1][1]
        gained = last - first
        elapsed_hr = max(0.5, (rows[-1][0] - rows[0][0]).total_seconds() / 3600)
        per_hr = gained / elapsed_hr
        lines.append(f"| {name} | {first} | {last} | **+{gained}** | {per_hr:.1f} |")
    lines.append("")

    # 時段分析
    lines.append("## 各時段增量分析")
    lines.append("")
    for name, rows in series.items():
        lines.append(f"### {name}")
        lines.append("")
        # 依小時 bucket 累加 delta
        by_hour: dict[int, list[int]] = {h: [] for h in range(24)}
        for ts, _v, d in rows:
            by_hour[ts.hour].append(d)
        lines.append("| 小時 | 觀測次數 | 期間總增量 | 平均增量/觀測 | 標記 |")
        lines.append("| ---: | ---: | ---: | ---: | :--- |")
        all_deltas = [d for ds in by_hour.values() for d in ds]
        if all_deltas:
            mu = mean(all_deltas)
            sd = pstdev(all_deltas) or 1.0
        else:
            mu, sd = 0.0, 1.0
        for h in range(24):
            ds = by_hour[h]
            if not ds:
                continue
            total = sum(ds)
            avg = total / len(ds)
            tags = []
            if is_overnight(h):
                tags.append("深夜")
            z = (avg - mu) / sd
            if z >= 2:
                tags.append("**異常高**")
            elif z >= 1:
                tags.append("偏高")
            tag_s = "、".join(tags) or ""
            lines.append(f"| {h:02d}:00 | {len(ds)} | {total} | {avg:.1f} | {tag_s} |")
        lines.append("")
        # 走勢圖
        vals = [v for _, v, _ in rows]
        lines.append("```")
        lines.append("票數走勢（左→右 = 舊→新）")
        lines.append(render_ascii_chart(vals))
        lines.append(f"    範圍：{min(vals)} → {max(vals)}")
        lines.append("```")
        lines.append("")

    # 異常時段交叉比對
    lines.append("## 可疑時段比對（深夜 vs 白天增量）")
    lines.append("")
    lines.append("| 候選人 | 深夜(00-06) 平均增量 | 白天(06-24) 平均增量 | 倍數 |")
    lines.append("| --- | ---: | ---: | ---: |")
    for name, rows in series.items():
        night = [d for ts, _v, d in rows if is_overnight(ts.hour)]
        day = [d for ts, _v, d in rows if not is_overnight(ts.hour)]
        n_avg = mean(night) if night else 0.0
        d_avg = mean(day) if day else 0.0
        ratio = (n_avg / d_avg) if d_avg else float("inf") if n_avg else 0.0
        ratio_s = f"{ratio:.2f}x" if d_avg else "N/A"
        lines.append(f"| {name} | {n_avg:.1f} | {d_avg:.1f} | {ratio_s} |")
    lines.append("")

    lines.append("## 原始資料")
    lines.append("")
    lines.append(f"- 完整時間序列檔案：`data/vote-history.jsonl`（共 {len(records)} 筆）")
    lines.append(f"- 最新快照：`data/last-snapshot.json`")
    lines.append("")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines), encoding="utf-8")
    return out_path


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--hours", type=int, default=24)
    ap.add_argument("--out", type=Path, default=None)
    args = ap.parse_args()

    records = load_records(DATA_FILE)
    out_path = args.out or (
        DEFAULT_OUT
        / f"vote-report-{datetime.now(TPE).strftime('%Y%m%d-%H%M')}.md"
    )
    p = write_report(records, args.hours, out_path)
    print(f"Report written: {p}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""擷取大橋頂級CAS越光米卡片圖，並把「我要投給它」按鈕加上紅框後存檔。"""
from pathlib import Path
from playwright.sync_api import sync_playwright

OUT = Path(__file__).resolve().parent.parent / "docs" / "img" / "da-qiao-card.png"
OUT.parent.mkdir(parents=True, exist_ok=True)

INJECT_CSS = """
() => {
  const card = document.querySelector('div.card-shell[data-name="大橋頂級CAS越光米"]');
  if (!card) return false;
  const btn = card.querySelector('.vote-btn');
  if (!btn) return false;
  // 紅色框 + 微微外擴讓按鈕更顯眼
  btn.style.position = 'relative';
  btn.style.outline = '4px solid #ef4444';
  btn.style.outlineOffset = '6px';
  btn.style.borderRadius = '6px';
  return true;
}
"""

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    ctx = browser.new_context(
        viewport={"width": 480, "height": 1400},
        device_scale_factor=2,
        user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
        locale="zh-TW",
    )
    page = ctx.new_page()
    page.goto("https://taiwanriceaward2026.com.tw/?view=non-xiang", wait_until="domcontentloaded", timeout=60000)
    page.wait_for_timeout(3000)
    page.wait_for_selector('.group-non-xiang:not(.is-hidden)', timeout=15000)
    page.wait_for_timeout(1500)

    el = page.locator('div.card-shell[data-name="大橋頂級CAS越光米"] > div.card').first
    el.scroll_into_view_if_needed()
    page.wait_for_timeout(600)

    ok = page.evaluate(INJECT_CSS)
    if not ok:
        print("WARNING: 無法注入紅框")
    page.wait_for_timeout(300)

    el.screenshot(path=str(OUT))
    print(f"saved {OUT}")
    browser.close()

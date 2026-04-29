#!/usr/bin/env python3
"""擷取大橋頂級CAS越光米卡片圖，存到 docs/img/da-qiao-card.png"""
from pathlib import Path
from playwright.sync_api import sync_playwright

OUT = Path(__file__).resolve().parent.parent / "docs" / "img" / "da-qiao-card.png"
OUT.parent.mkdir(parents=True, exist_ok=True)

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    ctx = browser.new_context(
        viewport={"width": 480, "height": 1200},
        device_scale_factor=2,
        user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
        locale="zh-TW",
    )
    page = ctx.new_page()
    page.goto("https://taiwanriceaward2026.com.tw/?view=non-xiang", wait_until="domcontentloaded", timeout=60000)
    page.wait_for_timeout(3000)
    # 等待非香米組顯示
    page.wait_for_selector('.group-non-xiang:not(.is-hidden)', timeout=15000)
    page.wait_for_timeout(1500)
    # 找出 id="13"（大橋）的卡 element
    el = page.locator('div.card-shell[data-name="大橋頂級CAS越光米"]').first
    el.scroll_into_view_if_needed()
    page.wait_for_timeout(800)
    el.screenshot(path=str(OUT))
    print(f"saved {OUT}")
    browser.close()

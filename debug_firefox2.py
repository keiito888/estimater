"""MonotaROとMisumiのページ構造を詳細確認"""
import re
import time
from playwright.sync_api import sync_playwright

def inspect():
    with sync_playwright() as pw:
        browser = pw.firefox.launch(headless=True)
        ctx = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:126.0) Gecko/20100101 Firefox/126.0",
            locale="ja-JP", viewport={"width": 1280, "height": 800},
        )
        page = ctx.new_page()

        # MonotaRO: 価格セレクタを特定する
        print("=== MonotaRO 価格セレクタ調査 ===")
        page.goto("https://www.monotaro.com/s/?c=&q=MY2N-D2+DC24", wait_until="domcontentloaded", timeout=30000)
        time.sleep(3)

        # よく使われる価格セレクタを試す
        for sel in [
            "[class*='price']", "[class*='Price']",
            "[data-testid*='price']", "[itemprop='price']",
            "span[class*='price']", "p[class*='price']",
            "li:first-child [class*='price']",
        ]:
            els = page.query_selector_all(sel)
            if els:
                texts = [e.inner_text()[:30] for e in els[:3]]
                print(f"  '{sel}': {texts}")

        # 検索結果の最初の商品へのリンクを探す
        print("\nリンク先を確認:")
        links = page.query_selector_all("a[href]")
        monotaro_product_links = []
        for l in links:
            href = l.get_attribute("href") or ""
            if re.search(r"/g/\d+|/p/\d+|/\d+/\d+\.html", href):
                monotaro_product_links.append(href)
        print("商品リンク候補:", monotaro_product_links[:5])

        time.sleep(2)

        # Misumi: ページ構造確認
        print("\n=== Misumi 価格セレクタ調査 ===")
        page.goto("https://jp.misumi-ec.com/vona2/result/?Keyword=NF30-CS+3P+5A", wait_until="networkidle", timeout=30000)
        time.sleep(2)

        for sel in [
            "[class*='price']", "[class*='Price']",
            "[data-price]", "[class*='cost']",
            "a[href*='detail']",
        ]:
            els = page.query_selector_all(sel)
            if els:
                texts = [e.inner_text()[:30] for e in els[:3]]
                hrefs = [e.get_attribute("href") for e in els[:3] if e.get_attribute("href")]
                print(f"  '{sel}': {texts} hrefs={hrefs[:2]}")

        browser.close()

inspect()

"""Firefoxで価格取得を試みるデバッグスクリプト"""
import re
import time
from playwright.sync_api import sync_playwright

def try_firefox():
    with sync_playwright() as pw:
        browser = pw.firefox.launch(headless=True)
        ctx = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:126.0) Gecko/20100101 Firefox/126.0",
            locale="ja-JP",
            viewport={"width": 1280, "height": 800},
        )
        page = ctx.new_page()

        # MonotaRO 検索
        print("--- MonotaRO ---")
        try:
            page.goto("https://www.monotaro.com/s/?c=&q=MY2N-D2+DC24", wait_until="domcontentloaded", timeout=30000)
            time.sleep(3)
            print("タイトル:", page.title())
            print("URL:", page.url)

            # 価格要素を探す
            price_text = page.inner_text("body")
            prices = re.findall(r'[¥￥]([\d,]+)', price_text)
            print("¥価格候補:", prices[:10])

            # 商品リンクを探す
            links = page.query_selector_all("a")
            product_links = [l.get_attribute("href") for l in links if l.get_attribute("href") and "/p/" in (l.get_attribute("href") or "")]
            print("商品リンク:", product_links[:3])

        except Exception as e:
            print("エラー:", e)

        time.sleep(2)

        # Misumi 検索
        print("\n--- Misumi ---")
        try:
            page.goto("https://jp.misumi-ec.com/vona2/result/?Keyword=NF30-CS+3P+5A", wait_until="networkidle", timeout=30000)
            time.sleep(2)
            print("タイトル:", page.title())
            print("URL:", page.url)

            price_text = page.inner_text("body")
            prices = re.findall(r'[¥￥]([\d,]+)', price_text)
            print("¥価格候補:", prices[:10])

        except Exception as e:
            print("エラー:", e)

        browser.close()

try_firefox()

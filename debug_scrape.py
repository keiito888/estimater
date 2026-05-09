"""MonotaRO・Misumiのページ構造を確認するデバッグスクリプト"""
import time
from playwright.sync_api import sync_playwright

def check_monotaro(part_number: str):
    with sync_playwright() as pw:
        browser = pw.chromium.launch(
            headless=True,
            args=["--disable-blink-features=AutomationControlled", "--disable-http2", "--no-sandbox"],
        )
        ctx = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            locale="ja-JP",
            viewport={"width": 1280, "height": 800},
        )
        page = ctx.new_page()
        url = f"https://www.monotaro.com/s/?c=&q={part_number.replace(' ', '+')}"
        print(f"\n--- MonotaRO: {url} ---")
        page.goto(url, wait_until="domcontentloaded", timeout=30000)
        time.sleep(2)

        print("タイトル:", page.title())
        print("現在URL:", page.url)

        # 商品ページへのリンクを探す
        for selector in ['a[href*="/p/"]', 'li.search-result a', '.item-figure a', '.c-item-box a']:
            els = page.query_selector_all(selector)
            if els:
                print(f"セレクタ '{selector}' でヒット: {len(els)} 件")
                for el in els[:2]:
                    print("  href:", el.get_attribute("href"))
            else:
                print(f"セレクタ '{selector}': ヒットなし")

        browser.close()


def check_misumi(part_number: str):
    with sync_playwright() as pw:
        browser = pw.chromium.launch(
            headless=True,
            args=["--disable-blink-features=AutomationControlled", "--disable-http2", "--no-sandbox"],
        )
        ctx = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            locale="ja-JP",
            viewport={"width": 1280, "height": 800},
        )
        page = ctx.new_page()
        url = f"https://jp.misumi-ec.com/vona2/result/?Keyword={part_number.replace(' ', '+')}"
        print(f"\n--- Misumi: {url} ---")
        page.goto(url, wait_until="domcontentloaded", timeout=30000)
        time.sleep(2)

        print("タイトル:", page.title())
        print("現在URL:", page.url)

        # セレクタ確認
        for selector in ['.c-search-result__item a', '.product-list__item a', 'a[href*="detail"]', 'a[href*="vona2/detail"]']:
            els = page.query_selector_all(selector)
            if els:
                print(f"セレクタ '{selector}' でヒット: {len(els)} 件")
                for el in els[:2]:
                    print("  href:", el.get_attribute("href"))
            else:
                print(f"セレクタ '{selector}': ヒットなし")

        browser.close()


if __name__ == "__main__":
    check_monotaro("MY2N-D2 DC24")
    check_misumi("NF30-CS 3P 5A")

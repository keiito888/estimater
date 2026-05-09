"""__NEXT_DATA__ から価格データを探すデバッグスクリプト"""
import json
import re
import time
import requests
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "ja,en-US;q=0.9,en;q=0.8",
}

session = requests.Session()
session.headers.update(HEADERS)

def check_next_data(url: str, label: str):
    print(f"\n=== {label} ===")
    r = session.get(url, timeout=20)
    print("Status:", r.status_code)
    soup = BeautifulSoup(r.text, "lxml")

    # __NEXT_DATA__ を探す
    script = soup.find("script", id="__NEXT_DATA__")
    if script:
        try:
            data = json.loads(script.string)
            text = json.dumps(data, ensure_ascii=False)
            # 価格っぽいキーを探す
            price_keys = re.findall(r'"(price|Price|unitPrice|listPrice|salePrice|priceJpy)["\s]*:\s*["\d]([^"]{0,30})', text)
            print("価格キー:", price_keys[:10])
            # 商品URLっぽいものを探す
            urls = re.findall(r'"/p/\d+[^"]{0,50}"', text)
            print("商品URL候補:", urls[:5])
        except Exception as e:
            print("JSON解析エラー:", e)
    else:
        print("__NEXT_DATA__ なし")
        # window.__NEXT_DATA__ 形式を試す
        for s in soup.find_all("script"):
            txt = s.get_text()
            if "__NEXT_DATA__" in txt or "priceJpy" in txt or "listPrice" in txt:
                print("関連スクリプト (先頭200文字):", txt[:200])
                break

# MonotaROの検索結果
check_next_data("https://www.monotaro.com/s/?c=&q=MY2N-D2+DC24", "MonotaRO 検索結果")
time.sleep(2)

# MonotaROで商品ページを直接試す (型番から推測)
check_next_data("https://www.monotaro.com/g/01207895/", "MonotaRO 商品ページ(例)")
time.sleep(2)

# Misumiの検索結果
check_next_data("https://jp.misumi-ec.com/vona2/result/?Keyword=NF30-CS+3P+5A", "Misumi 検索結果")

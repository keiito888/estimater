"""MonotaROの価格データ取得方法を調査"""
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

# MonotaROの検索結果から型番の商品コードを探す
print("=== MonotaRO 検索ページ (MY2N-D2 DC24) ===")
r = session.get("https://www.monotaro.com/s/?c=&q=MY2N-D2+DC24", timeout=20)
soup = BeautifulSoup(r.text, "lxml")

# __next_f データを全部集める
all_next_f = []
for s in soup.find_all("script"):
    txt = s.get_text()
    if "__next_f" in txt:
        all_next_f.append(txt)

print(f"__next_f スクリプト数: {len(all_next_f)}")
for i, txt in enumerate(all_next_f[:3]):
    print(f"\n--- スクリプト {i} (先頭300文字) ---")
    print(txt[:300])

# 商品コードを探す
product_codes = re.findall(r'"productCode"\s*:\s*(\d+)', r.text)
print("\n商品コード候補:", product_codes[:5])

# 価格を探す
prices = re.findall(r'"(price|Price|listPrice|priceJpy|unitPrice)"\s*:\s*(\d+)', r.text)
print("価格候補:", prices[:10])

# MonotaROの内部API試行
time.sleep(1)
print("\n=== MonotaRO 商品ページ直接 ===")
# 検索URL (Misumiなどと同様に type 番号のURLでアクセス)
r2 = session.get("https://www.monotaro.com/p/0243/0763/", timeout=20)
print("Status:", r2.status_code, "URL:", r2.url)
prices2 = re.findall(r'"(price|listPrice|priceJpy)"\s*:\s*"?(\d+)"?', r2.text)
print("価格候補:", prices2[:10])

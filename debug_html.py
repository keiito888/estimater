"""実際のHTMLを確認するデバッグスクリプト"""
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

# --- MonotaRO ---
print("=== MonotaRO 検索結果 ===")
r = session.get("https://www.monotaro.com/s/?c=&q=MY2N-D2+DC24", timeout=15)
print("Status:", r.status_code, "URL:", r.url)
soup = BeautifulSoup(r.text, "lxml")
print("タイトル:", soup.title.get_text() if soup.title else "なし")

# /p/ を含むリンクを探す
links_p = [a["href"] for a in soup.find_all("a", href=True) if "/p/" in a["href"]]
print("'/p/' リンク数:", len(links_p))
for l in links_p[:5]:
    print(" ", l)

# HTMLの最初の1000文字
print("\nHTML先頭1000文字:")
print(r.text[:1000])
print("...")

time.sleep(2)

# --- Misumi ---
print("\n=== Misumi 検索結果 ===")
r2 = session.get("https://jp.misumi-ec.com/vona2/result/?Keyword=NF30-CS+3P+5A", timeout=15)
print("Status:", r2.status_code, "URL:", r2.url)
soup2 = BeautifulSoup(r2.text, "lxml")
print("タイトル:", soup2.title.get_text() if soup2.title else "なし")

links_d = [a["href"] for a in soup2.find_all("a", href=True) if "detail" in a["href"]]
print("'detail' リンク数:", len(links_d))
for l in links_d[:5]:
    print(" ", l)

print("\nHTML先頭1000文字:")
print(r2.text[:1000])

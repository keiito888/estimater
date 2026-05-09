"""MonotaRO (www.monotaro.com) から型番で価格を取得するスクレイパー (Firefox版)"""

import re
import time
from typing import Optional
from playwright.sync_api import Page

from ..models import PriceResult
from ..config import scrape_delay

SEARCH_URL = "https://www.monotaro.com/s/?c=&q={part_number}"


def fetch_price(page: Page, part_number: str) -> PriceResult:
    """MonotaROで型番を検索し、単価を返す"""
    if page is None:
        return PriceResult(
            part_number=part_number, unit_price=None, source="monotaro",
            error="ブラウザが初期化されていません",
        )
    url = SEARCH_URL.format(part_number=part_number.replace(" ", "+"))
    try:
        page.goto(url, wait_until="domcontentloaded", timeout=30000)
        time.sleep(2)  # JS描画を待つ
        scrape_delay()

        # 商品グループリンク /g/XXXXXXXX/ を探して商品ページへ
        links = page.query_selector_all("a[href]")
        product_url: Optional[str] = None
        for link in links:
            href = link.get_attribute("href") or ""
            if re.search(r"/g/\d+/", href):
                product_url = f"https://www.monotaro.com{href}" if href.startswith("/") else href
                break

        if not product_url:
            # 検索結果ページ自体に価格がある場合
            return _extract_price_from_page(page, part_number, url)

        # 商品ページへ移動
        page.goto(product_url, wait_until="domcontentloaded", timeout=30000)
        time.sleep(2)
        scrape_delay()

        return _extract_price_from_page(page, part_number, product_url)

    except Exception as e:
        return PriceResult(part_number=part_number, unit_price=None, source="monotaro", error=str(e))


def _extract_price_from_page(page: Page, part_number: str, url: str) -> PriceResult:
    """ページから価格・商品名を取得する"""
    unit_price: Optional[float] = None
    product_name: Optional[str] = None

    # 商品名
    h1 = page.query_selector("h1")
    if h1:
        product_name = h1.inner_text().strip()

    # 価格セレクタ (MonotaROは [class*='Price'] に価格を含む)
    price_els = page.query_selector_all("[class*='Price'], [class*='price'], [itemprop='price']")
    for el in price_els:
        text = el.inner_text()
        price = _extract_price_from_text(text)
        if price and price > 10:
            unit_price = price
            break

    # セレクタで見つからない場合、ページ全体のテキストから探す
    if unit_price is None:
        body_text = page.inner_text("body")
        matches = re.findall(r"[¥￥]([\d,]+)", body_text)
        for m in matches:
            try:
                val = float(m.replace(",", ""))
                if 10 < val < 10_000_000:
                    unit_price = val
                    break
            except ValueError:
                continue

    return PriceResult(
        part_number=part_number,
        unit_price=unit_price,
        source="monotaro",
        product_name=product_name,
        url=url,
        error=None if unit_price is not None else "価格が見つかりませんでした",
    )


def _extract_price_from_text(text: str) -> Optional[float]:
    """テキストから価格数値を抽出する"""
    matches = re.findall(r"([\d,]+)円|[¥￥]([\d,]+)", text)
    for m in matches:
        num_str = (m[0] or m[1]).replace(",", "")
        try:
            val = float(num_str)
            if 10 < val < 10_000_000:
                return val
        except ValueError:
            continue
    return None

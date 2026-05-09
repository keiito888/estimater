"""Amazon.co.jp から型番で価格を取得するスクレイパー"""

import re
import time
from typing import Optional
from playwright.sync_api import Page

from ..models import PriceResult
from ..config import scrape_delay

SEARCH_URL = "https://www.amazon.co.jp/s?k={part_number}"


def fetch_price(page: Page, part_number: str) -> PriceResult:
    """Amazonで型番を検索し、最初の商品の価格を返す"""
    url = SEARCH_URL.format(part_number=part_number.replace(" ", "+"))
    try:
        page.goto(url, wait_until="domcontentloaded", timeout=30000)
        time.sleep(2)
        scrape_delay()

        # 検索結果から最初の商品の価格を取得
        unit_price = _extract_first_price(page)
        product_name = _extract_first_product_name(page)
        product_url = _extract_first_product_url(page)

        # 価格が見つかった場合は商品ページへ移動して確認
        if not unit_price and product_url:
            page.goto(product_url, wait_until="domcontentloaded", timeout=25000)
            time.sleep(2)
            unit_price = _extract_detail_price(page)
            if not product_name:
                h1 = page.query_selector("h1#title, #productTitle")
                if h1:
                    product_name = h1.inner_text().strip()
            product_url = page.url

        return PriceResult(
            part_number=part_number,
            unit_price=unit_price,
            source="amazon",
            product_name=product_name,
            url=product_url or url,
            error=None if unit_price else "価格が見つかりませんでした",
        )

    except Exception as e:
        return PriceResult(part_number=part_number, unit_price=None, source="amazon", error=str(e))


def _extract_first_price(page: Page) -> Optional[float]:
    """検索結果ページの最初の商品価格を取得"""
    # Amazon 検索結果の価格セレクタ
    for sel in [
        ".a-price .a-offscreen",
        "[data-component-type='s-search-result'] .a-price-whole",
        ".s-result-item .a-price .a-offscreen",
    ]:
        el = page.query_selector(sel)
        if el:
            price = _parse_price(el.inner_text())
            if price and price > 10:
                return price
    return None


def _extract_first_product_name(page: Page) -> Optional[str]:
    el = page.query_selector("[data-component-type='s-search-result'] h2 a span")
    return el.inner_text().strip() if el else None


def _extract_first_product_url(page: Page) -> Optional[str]:
    el = page.query_selector("[data-component-type='s-search-result'] h2 a")
    if el:
        href = el.get_attribute("href") or ""
        return href if href.startswith("http") else f"https://www.amazon.co.jp{href}"
    return None


def _extract_detail_price(page: Page) -> Optional[float]:
    """商品詳細ページから価格を取得"""
    for sel in ["#priceblock_ourprice", "#priceblock_dealprice",
                ".a-price .a-offscreen", "#price_inside_buybox"]:
        el = page.query_selector(sel)
        if el:
            price = _parse_price(el.inner_text())
            if price and price > 10:
                return price
    return None


def _parse_price(text: str) -> Optional[float]:
    cleaned = re.sub(r"[^\d]", "", str(text).split(".")[0])
    try:
        val = float(cleaned) if cleaned else None
        return val if val and val > 0 else None
    except ValueError:
        return None

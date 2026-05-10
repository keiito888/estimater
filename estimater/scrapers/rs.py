"""RS Components (jp.rs-online.com) から型番で価格を取得するスクレイパー"""

import re
import time
from typing import Optional
from playwright.sync_api import Page

from ..models import PriceResult
from ..config import scrape_delay
from .utils import part_number_in_page

SEARCH_URL = "https://jp.rs-online.com/web/c/?searchTerm={part_number}"


def fetch_price(page: Page, part_number: str) -> PriceResult:
    """RS Componentsで型番を検索し、単価を返す"""
    url = SEARCH_URL.format(part_number=part_number.replace(" ", "+"))
    try:
        page.goto(url, wait_until="domcontentloaded", timeout=30000)
        time.sleep(2)
        scrape_delay()

        current_url = page.url

        # 直接商品ページに遷移した場合
        if "/web/p/" in current_url:
            return _extract_from_page(page, part_number, current_url)

        # 検索結果から型番に一致する商品リンクをたどる（上位5件）
        links = page.query_selector_all("a[href*='/web/p/']")
        for link in links[:5]:
            href = link.get_attribute("href") or ""
            product_url = href if href.startswith("http") else f"https://jp.rs-online.com{href}"
            page.goto(product_url, wait_until="domcontentloaded", timeout=25000)
            time.sleep(2)
            if part_number_in_page(part_number, page.inner_text("body")):
                return _extract_from_page(page, part_number, page.url)

        # 検索結果ページ自体に価格がある場合
        return _extract_from_page(page, part_number, current_url)

    except Exception as e:
        return PriceResult(part_number=part_number, unit_price=None, source="rs", error=str(e))


def _extract_from_page(page: Page, part_number: str, url: str) -> PriceResult:
    product_name: Optional[str] = None
    unit_price: Optional[float] = None

    h1 = page.query_selector("h1")
    if h1:
        product_name = h1.inner_text().strip()

    # 価格セレクタ
    for sel in ["[class*='price']", "[class*='Price']", "[data-testid*='price']"]:
        els = page.query_selector_all(sel)
        for el in els:
            price = _parse_price(el.inner_text())
            if price and price > 10:
                unit_price = price
                break
        if unit_price:
            break

    if unit_price is None:
        body = page.inner_text("body")
        prices = re.findall(r"[¥￥]([\d,]+)", body)
        for p in prices:
            val = _parse_price(p)
            if val and val > 10:
                unit_price = val
                break

    return PriceResult(
        part_number=part_number,
        unit_price=unit_price,
        source="rs",
        product_name=product_name,
        url=url,
        error=None if unit_price else "価格が見つかりませんでした",
    )


def _parse_price(text: str) -> Optional[float]:
    cleaned = re.sub(r"[^\d]", "", str(text).split(".")[0])
    try:
        val = float(cleaned) if cleaned else None
        return val if val and val > 0 else None
    except ValueError:
        return None

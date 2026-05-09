"""TRUSCO (trusco.co.jp) から型番で価格を取得するスクレイパー"""

import re
import time
from typing import Optional
from playwright.sync_api import Page

from ..models import PriceResult
from ..config import scrape_delay

# TRUSCOは工具・機械部品が主力のため、電気部品の取り扱いは限定的
SEARCH_URL = "https://www.trusco.co.jp/search?q={part_number}"
SEARCH_URL_ALT = "https://www.trusco.co.jp/result?searchStr={part_number}&searchType=1"


def fetch_price(page: Page, part_number: str) -> PriceResult:
    """TRUSCOで型番を検索し、単価を返す"""
    encoded = part_number.replace(" ", "+")
    url = SEARCH_URL.format(part_number=encoded)
    try:
        page.goto(url, wait_until="domcontentloaded", timeout=30000)
        time.sleep(2)
        scrape_delay()

        current_url = page.url

        # トップページにリダイレクトされた場合は代替URLを試す
        if current_url == "https://www.trusco.co.jp/" or "result" not in current_url:
            alt_url = SEARCH_URL_ALT.format(part_number=encoded)
            page.goto(alt_url, wait_until="domcontentloaded", timeout=25000)
            time.sleep(2)
            current_url = page.url

        return _extract_from_page(page, part_number, current_url)

    except Exception as e:
        return PriceResult(part_number=part_number, unit_price=None, source="trusco", error=str(e))


def _extract_from_page(page: Page, part_number: str, url: str) -> PriceResult:
    product_name: Optional[str] = None
    unit_price: Optional[float] = None

    h1 = page.query_selector("h1")
    if h1:
        product_name = h1.inner_text().strip()

    for sel in ["[class*='price']", "[class*='Price']", "[class*='cost']"]:
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
        source="trusco",
        product_name=product_name,
        url=url,
        error=None if unit_price else "商品が見つかりませんでした（TRUSCOは電気部品の取り扱いが限定的です）",
    )


def _parse_price(text: str) -> Optional[float]:
    cleaned = re.sub(r"[^\d]", "", str(text).split(".")[0])
    try:
        val = float(cleaned) if cleaned else None
        return val if val and val > 0 else None
    except ValueError:
        return None

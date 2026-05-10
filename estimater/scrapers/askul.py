"""アスクル (askul.co.jp) から型番で価格を取得するスクレイパー"""

import re
import time
from typing import Optional
from playwright.sync_api import Page

from ..models import PriceResult
from ..config import scrape_delay
from .utils import part_number_in_page

SEARCH_URL = "https://www.askul.co.jp/f/search/?word={part_number}"


def fetch_price(page: Page, part_number: str) -> PriceResult:
    """アスクルで型番を検索し、単価を返す"""
    url = SEARCH_URL.format(part_number=part_number.replace(" ", "+"))
    try:
        page.goto(url, wait_until="domcontentloaded", timeout=30000)
        time.sleep(2)
        scrape_delay()

        # 検索結果リンクを複数取得し、型番を含む商品を探す
        links = page.query_selector_all("a[href*='/p/']")
        if not links:
            return PriceResult(
                part_number=part_number, unit_price=None, source="askul",
                error="商品が見つかりませんでした",
            )

        for link in links[:5]:  # 上位5件を確認
            href = link.get_attribute("href") or ""
            product_url = (
                "https://www.askul.co.jp" + href if href.startswith("/") else href
            )
            page.goto(product_url, wait_until="domcontentloaded", timeout=25000)
            time.sleep(1)

            if part_number_in_page(part_number, page.inner_text("body")):
                scrape_delay()
                return _extract_from_page(page, part_number, page.url)

        # 型番が一致する商品が見つからなかった
        return PriceResult(
            part_number=part_number,
            unit_price=None,
            source="askul",
            error="型番に一致する商品が見つかりませんでした",
        )

    except Exception as e:
        return PriceResult(
            part_number=part_number, unit_price=None, source="askul", error=str(e)
        )


def _extract_from_page(page: Page, part_number: str, url: str) -> PriceResult:
    product_name: Optional[str] = None
    unit_price: Optional[float] = None

    h1 = page.query_selector("h1")
    if h1:
        product_name = h1.inner_text().strip()

    # アスクルの価格セレクタ
    for sel in ["[class*='price']", "[class*='Price']", "[itemprop='price']"]:
        els = page.query_selector_all(sel)
        for el in els:
            price = _parse_price(el.inner_text())
            if price and price > 10:
                unit_price = price
                break
        if unit_price:
            break

    # セレクタで見つからない場合はページ全体から
    if unit_price is None:
        body = page.inner_text("body")
        for m in re.findall(r"[￥¥]([\d,]+)", body):
            val = _parse_price(m)
            if val and val > 10:
                unit_price = val
                break

    return PriceResult(
        part_number=part_number,
        unit_price=unit_price,
        source="askul",
        product_name=product_name,
        url=url,
        error=None if unit_price else "価格が見つかりませんでした",
    )


def _parse_price(text: str) -> Optional[float]:
    # 「税込」「税抜」などを除去して数値だけ取る
    cleaned = re.sub(r"[^\d]", "", str(text).split("（")[0].split("(")[0])
    try:
        val = float(cleaned) if cleaned else None
        return val if val and val > 0 else None
    except ValueError:
        return None

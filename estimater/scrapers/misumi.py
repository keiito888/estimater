"""Misumi (jp.misumi-ec.com) から型番で価格を取得するスクレイパー (Firefox版)"""

import re
import time
from typing import Optional
from playwright.sync_api import Page

from ..models import PriceResult
from ..config import scrape_delay
from .session import has_misumi_session

SEARCH_URL = "https://jp.misumi-ec.com/vona2/result/?Keyword={part_number}"


def fetch_price(page: Page, part_number: str) -> PriceResult:
    """Misumiで型番を検索し、単価を返す"""
    if page is None:
        return PriceResult(
            part_number=part_number, unit_price=None, source="misumi",
            error="ブラウザが初期化されていません",
        )
    if not has_misumi_session():
        return PriceResult(
            part_number=part_number, unit_price=None, source="misumi",
            error="Misumiにログインしていません。'py -m estimater login misumi' を実行してください",
        )
    url = SEARCH_URL.format(part_number=part_number.replace(" ", "+"))
    try:
        page.goto(url, wait_until="networkidle", timeout=30000)
        scrape_delay()
        return _extract_from_search_page(page, part_number, url)
    except Exception as e:
        return PriceResult(part_number=part_number, unit_price=None, source="misumi", error=str(e))


def _extract_from_search_page(page: Page, part_number: str, url: str) -> PriceResult:
    """検索結果ページから直接価格を取得する"""
    unit_price: Optional[float] = None
    product_name: Optional[str] = None
    detail_url: Optional[str] = None

    # 商品名と詳細URLを取得
    detail_link = page.query_selector("a[href*='detail']")
    if detail_link:
        product_name = detail_link.inner_text().strip()
        detail_url = detail_link.get_attribute("href")

    # 価格を取得: [class*='Price'] の中から数字を抽出
    price_els = page.query_selector_all("[class*='Price'], [class*='price']")
    for el in price_els:
        text = el.inner_text()
        price = _extract_price_from_text(text)
        if price and price > 10:
            unit_price = price
            break

    # 見つからなければ詳細ページへ
    if unit_price is None and detail_url:
        try:
            page.goto(detail_url, wait_until="networkidle", timeout=30000)
            scrape_delay()
            price_els2 = page.query_selector_all("[class*='Price'], [class*='price']")
            for el in price_els2:
                text = el.inner_text()
                price = _extract_price_from_text(text)
                if price and price > 10:
                    unit_price = price
                    break
        except Exception:
            pass

    return PriceResult(
        part_number=part_number,
        unit_price=unit_price,
        source="misumi",
        product_name=product_name,
        url=detail_url or url,
        error=None if unit_price is not None else "価格が見つかりませんでした（ログイン必要な可能性あり）",
    )


def _extract_price_from_text(text: str) -> Optional[float]:
    """テキストから価格数値を抽出する"""
    # 「4,860円」「¥4,860」「4,860」などにマッチ
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

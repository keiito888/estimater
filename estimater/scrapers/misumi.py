"""Misumi (jp.misumi-ec.com) から型番で価格を取得するスクレイパー"""

import re
from typing import Optional
from playwright.sync_api import Page
from ..models import PriceResult
from ..config import scrape_delay


SEARCH_URL = "https://jp.misumi-ec.com/vona2/result/?Keyword={part_number}"
PRICE_SELECTORS = [
    ".price-block__price",
    ".ec-price__number",
    "[class*='price'] [class*='number']",
    "[class*='Price'] [class*='value']",
]


def fetch_price(page: Page, part_number: str) -> PriceResult:
    """
    Misumiで型番を検索し、単価を返す。
    取得できない場合は unit_price=None で返す。
    """
    url = SEARCH_URL.format(part_number=part_number.replace(" ", "+"))
    try:
        page.goto(url, wait_until="domcontentloaded", timeout=20000)
        scrape_delay()

        # 検索結果ページか商品ページかを判定
        # 型番が完全一致する場合は商品ページに直接遷移することがある
        current_url = page.url
        if "vona2/detail" in current_url or "detail" in current_url:
            return _extract_from_detail_page(page, part_number, current_url)

        # 検索結果一覧から最初のアイテムをクリック
        first_item = page.query_selector(".c-search-result__item a, .product-list__item a")
        if first_item:
            first_item.click()
            page.wait_for_load_state("domcontentloaded", timeout=15000)
            scrape_delay()
            return _extract_from_detail_page(page, part_number, page.url)

        return PriceResult(
            part_number=part_number,
            unit_price=None,
            source="misumi",
            error="検索結果が見つかりませんでした",
        )

    except Exception as e:
        return PriceResult(
            part_number=part_number,
            unit_price=None,
            source="misumi",
            error=str(e),
        )


def _extract_from_detail_page(page: Page, part_number: str, url: str) -> PriceResult:
    """商品詳細ページから価格・商品名を抽出する"""
    product_name: Optional[str] = None
    unit_price: Optional[float] = None

    # 商品名取得
    name_el = page.query_selector("h1, .product-name, [class*='product-title']")
    if name_el:
        product_name = name_el.inner_text().strip()

    # 価格取得 (複数セレクタを試す)
    for selector in PRICE_SELECTORS:
        el = page.query_selector(selector)
        if el:
            text = el.inner_text().strip()
            price = _parse_price(text)
            if price is not None:
                unit_price = price
                break

    # セレクタで取れない場合、テキスト全体から正規表現で探す
    if unit_price is None:
        body_text = page.inner_text("body")
        unit_price = _find_price_in_text(body_text)

    return PriceResult(
        part_number=part_number,
        unit_price=unit_price,
        source="misumi",
        product_name=product_name,
        url=url,
        error=None if unit_price is not None else "価格要素が見つかりませんでした",
    )


def _parse_price(text: str) -> Optional[float]:
    """「¥1,234」「1,234円」などから数値を抽出する"""
    cleaned = re.sub(r"[^\d,.]", "", text.replace(",", ""))
    try:
        return float(cleaned) if cleaned else None
    except ValueError:
        return None


def _find_price_in_text(text: str) -> Optional[float]:
    """ページ全文から「¥数字」パターンを探す"""
    matches = re.findall(r"[¥￥]\s*([\d,]+)", text)
    for m in matches:
        try:
            val = float(m.replace(",", ""))
            if val > 0:
                return val
        except ValueError:
            continue
    return None

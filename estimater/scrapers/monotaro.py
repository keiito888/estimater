"""MonotaRO (www.monotaro.com) から型番で価格を取得するスクレイパー"""

import re
from typing import Optional
from playwright.sync_api import Page
from ..models import PriceResult
from ..config import scrape_delay


SEARCH_URL = "https://www.monotaro.com/s/?c=&q={part_number}"
PRICE_SELECTORS = [
    ".price-block .price",
    "[class*='price__value']",
    "[class*='itemPrice']",
    ".monotaro-price",
    "[itemprop='price']",
]


def fetch_price(page: Page, part_number: str) -> PriceResult:
    """
    MonotaROで型番を検索し、単価を返す。
    取得できない場合は unit_price=None で返す。
    """
    url = SEARCH_URL.format(part_number=part_number.replace(" ", "+"))
    try:
        page.goto(url, wait_until="domcontentloaded", timeout=20000)
        scrape_delay()

        # 検索結果から最初の商品ページへ遷移
        first_item = page.query_selector(
            ".item-figure a, .search-result-item a[href*='/p/'], li.search-result a"
        )
        if first_item:
            href = first_item.get_attribute("href")
            if href:
                product_url = href if href.startswith("http") else f"https://www.monotaro.com{href}"
                page.goto(product_url, wait_until="domcontentloaded", timeout=20000)
                scrape_delay()
                return _extract_from_detail_page(page, part_number, page.url)

        # 直接商品ページに遷移した場合
        if "/p/" in page.url:
            return _extract_from_detail_page(page, part_number, page.url)

        return PriceResult(
            part_number=part_number,
            unit_price=None,
            source="monotaro",
            error="検索結果が見つかりませんでした",
        )

    except Exception as e:
        return PriceResult(
            part_number=part_number,
            unit_price=None,
            source="monotaro",
            error=str(e),
        )


def _extract_from_detail_page(page: Page, part_number: str, url: str) -> PriceResult:
    """商品詳細ページから価格・商品名を抽出する"""
    product_name: Optional[str] = None
    unit_price: Optional[float] = None

    # 商品名取得
    name_el = page.query_selector("h1.item-heading, h1[class*='item'], .product-name h1")
    if not name_el:
        name_el = page.query_selector("h1")
    if name_el:
        product_name = name_el.inner_text().strip()

    # 価格取得
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
        source="monotaro",
        product_name=product_name,
        url=url,
        error=None if unit_price is not None else "価格要素が見つかりませんでした",
    )


def _parse_price(text: str) -> Optional[float]:
    """「¥1,234」「1,234円」などから数値を抽出する"""
    cleaned = re.sub(r"[^\d]", "", text.split(".")[0])
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

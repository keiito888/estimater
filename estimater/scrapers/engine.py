"""価格取得エンジン: Misumi優先 → MonotaROフォールバック"""

from typing import Optional
from playwright.sync_api import sync_playwright, Browser, BrowserContext, Page
from ..models import Part, PriceResult
from ..config import is_headless
from . import misumi, monotaro


def fetch_prices(parts: list[Part], cache: dict[str, PriceResult]) -> list[PriceResult]:
    """
    部品リストの価格を一括取得する。
    キャッシュに存在する型番はスクレイピングをスキップする。
    """
    results: list[PriceResult] = []
    uncached = [p for p in parts if p.part_number not in cache]

    if not uncached:
        for part in parts:
            result = cache[part.part_number]
            result.source = "cache"
            results.append(result)
        return results

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=is_headless())
        context = _create_context(browser)
        page = context.new_page()

        for part in parts:
            if part.part_number in cache:
                cached = cache[part.part_number]
                cached.source = "cache"
                results.append(cached)
                continue

            result = _fetch_single(page, part)
            results.append(result)

        browser.close()

    return results


def _fetch_single(page: Page, part: Part) -> PriceResult:
    """1部品の価格を仕入先希望に従って取得する"""
    source = part.preferred_source.lower().strip()

    if source == "misumi":
        result = misumi.fetch_price(page, part.part_number)
        if result.unit_price is None:
            # フォールバック
            result = monotaro.fetch_price(page, part.part_number)
    elif source == "monotaro":
        result = monotaro.fetch_price(page, part.part_number)
        if result.unit_price is None:
            result = misumi.fetch_price(page, part.part_number)
    else:
        # 仕入先未指定: Misumi優先
        result = misumi.fetch_price(page, part.part_number)
        if result.unit_price is None:
            result = monotaro.fetch_price(page, part.part_number)

    return result


def _create_context(browser: Browser) -> BrowserContext:
    """一般的なブラウザに見えるようにコンテキストを設定する"""
    return browser.new_context(
        user_agent=(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        ),
        locale="ja-JP",
        timezone_id="Asia/Tokyo",
        viewport={"width": 1280, "height": 800},
    )

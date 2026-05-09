"""価格取得エンジン: Firefox使用、Misumi優先 → MonotaROフォールバック"""

from playwright.sync_api import sync_playwright, Browser, BrowserContext, Page

from ..models import Part, PriceResult
from ..config import is_headless
from . import misumi, monotaro


def fetch_prices(parts: list[Part], cache: dict[str, PriceResult]) -> list[PriceResult]:
    """
    部品リストの価格を一括取得する。
    キャッシュに存在する型番はスクレイピングをスキップする。
    """
    uncached = [p for p in parts if p.part_number not in cache]
    results: list[PriceResult] = []

    if uncached:
        with sync_playwright() as pw:
            # Firefox を使用 (Chromiumよりボット検出を受けにくい)
            browser = pw.firefox.launch(headless=is_headless())
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
    else:
        for part in parts:
            cached = cache[part.part_number]
            cached.source = "cache"
            results.append(cached)

    return results


def _fetch_single(page: Page, part: Part) -> PriceResult:
    """1部品の価格を仕入先希望に従って取得する"""
    source = part.preferred_source.lower().strip()

    if source == "misumi":
        result = misumi.fetch_price(page, part.part_number)
        if result.unit_price is None:
            fallback = monotaro.fetch_price(page, part.part_number)
            return fallback if fallback.unit_price is not None else result

    elif source == "monotaro":
        result = monotaro.fetch_price(page, part.part_number)
        if result.unit_price is None:
            fallback = misumi.fetch_price(page, part.part_number)
            return fallback if fallback.unit_price is not None else result

    else:
        # 仕入先未指定: Misumi優先
        result = misumi.fetch_price(page, part.part_number)
        if result.unit_price is None:
            fallback = monotaro.fetch_price(page, part.part_number)
            return fallback if fallback.unit_price is not None else result

    return result


def _create_context(browser: Browser) -> BrowserContext:
    """Firefox コンテキストを設定する"""
    return browser.new_context(
        user_agent=(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:126.0) "
            "Gecko/20100101 Firefox/126.0"
        ),
        locale="ja-JP",
        timezone_id="Asia/Tokyo",
        viewport={"width": 1280, "height": 800},
        extra_http_headers={
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "ja,en-US;q=0.9,en;q=0.8",
            "DNT": "1",
        },
    )

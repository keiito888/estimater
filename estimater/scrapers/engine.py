"""価格取得エンジン: 複数ソースから価格を取得して最安値を選択"""

from playwright.sync_api import sync_playwright, Browser, BrowserContext, Page

from ..models import Part, PriceResult
from ..config import is_headless
from . import misumi, monotaro, rs, amazon, digikey, trusco
from .session import load_misumi_session, has_misumi_session

# 仕入先名 → スクレイパーモジュールのマッピング
SCRAPERS = {
    "monotaro": monotaro,
    "rs":        rs,
    "amazon":    amazon,
    "digikey":   digikey,
    "trusco":    trusco,
    "misumi":    misumi,
}

# 仕入先未指定時に試すソースの優先順
DEFAULT_SOURCES = ["monotaro", "rs", "amazon", "digikey", "trusco"]


def fetch_prices(parts: list[Part], cache: dict[str, PriceResult]) -> list[PriceResult]:
    """
    部品リストの価格を一括取得する。
    キャッシュ・手動入力済みの型番はスクレイピングをスキップする。
    """
    # 手動単価が入力済みの部品
    manual_results: dict[str, PriceResult] = {
        part.part_number: PriceResult(
            part_number=part.part_number,
            unit_price=part.manual_price,
            source="手動入力",
        )
        for part in parts if part.manual_price is not None
    }

    uncached = [
        p for p in parts
        if p.part_number not in cache and p.manual_price is None
    ]

    results: list[PriceResult] = []

    if uncached:
        with sync_playwright() as pw:
            browser = pw.firefox.launch(headless=is_headless())
            session_state = load_misumi_session() if has_misumi_session() else None
            context = _create_context(browser, storage_state=session_state)
            page = context.new_page()

            for part in parts:
                if part.manual_price is not None:
                    results.append(manual_results[part.part_number])
                elif part.part_number in cache:
                    cached = cache[part.part_number]
                    cached.from_cache = True
                    results.append(cached)
                else:
                    results.append(_fetch_single(page, part))

            browser.close()
    else:
        for part in parts:
            if part.manual_price is not None:
                results.append(manual_results[part.part_number])
            else:
                cached = cache[part.part_number]
                cached.from_cache = True
                results.append(cached)

    return results


def _fetch_single(page: Page, part: Part) -> PriceResult:
    """
    1部品の価格を取得する。
    - 仕入先指定あり: 指定先で取得、失敗時は他ソースにフォールバック
    - 仕入先指定なし: 全ソースを試して最安値を返す
    """
    source = part.preferred_source.lower().strip()

    if source and source in SCRAPERS:
        # 指定仕入先で取得
        result = SCRAPERS[source].fetch_price(page, part.part_number)
        if result.unit_price is not None:
            return result
        # 失敗したら他ソースを試す
        for fallback_name in DEFAULT_SOURCES:
            if fallback_name == source:
                continue
            fb = SCRAPERS[fallback_name].fetch_price(page, part.part_number)
            if fb.unit_price is not None:
                return fb
        return result  # 全て失敗した場合は最初のエラーを返す

    else:
        # 仕入先未指定: 全ソースで取得して最安値を選択
        found: list[PriceResult] = []
        for src_name in DEFAULT_SOURCES:
            r = SCRAPERS[src_name].fetch_price(page, part.part_number)
            if r.unit_price is not None:
                found.append(r)

        if found:
            # 最安値を返す
            return min(found, key=lambda r: r.unit_price)

        # 全て失敗
        return PriceResult(
            part_number=part.part_number,
            unit_price=None,
            source="",
            error="全ての検索先で価格が見つかりませんでした",
        )


def _create_context(
    browser: Browser, storage_state: dict | None = None
) -> BrowserContext:
    kwargs = dict(
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
    if storage_state:
        kwargs["storage_state"] = storage_state
    return browser.new_context(**kwargs)

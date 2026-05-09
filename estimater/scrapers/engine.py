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

# キャッシュの型: {型番: {仕入先: PriceResult}}
CacheType = dict[str, dict[str, PriceResult]]


def fetch_prices(
    parts: list[Part],
    cache: CacheType,
) -> tuple[list[PriceResult], list[PriceResult]]:
    """
    部品リストの価格を取得する。

    - 仕入先ごとにキャッシュを確認し、未キャッシュのソースのみスクレイピング。
    - 全ソースの結果（キャッシュ + 新規取得）を比較して最安値を選択。

    戻り値:
        results:        各部品の最安値 PriceResult のリスト (見積書に使用)
        newly_scraped:  今回新規に取得した PriceResult のリスト (キャッシュ保存用)
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

    # スクレイピングが必要な (部品, ソース) のペアを収集
    scrape_needed: list[tuple[Part, str]] = []
    for part in parts:
        if part.manual_price is not None:
            continue
        sources_to_try = _sources_for_part(part)
        part_cache = cache.get(part.part_number, {})
        for src in sources_to_try:
            if src not in part_cache:
                scrape_needed.append((part, src))

    # スクレイピング実行
    newly_scraped: list[PriceResult] = []
    if scrape_needed:
        with sync_playwright() as pw:
            browser = pw.firefox.launch(headless=is_headless())
            session_state = load_misumi_session() if has_misumi_session() else None
            context = _create_context(browser, storage_state=session_state)
            page = context.new_page()

            for part, src in scrape_needed:
                result = SCRAPERS[src].fetch_price(page, part.part_number)
                newly_scraped.append(result)

            browser.close()

    # 新規取得結果をキャッシュ辞書にマージ（この関数内での一時マージ）
    merged_cache: CacheType = {pn: dict(srcs) for pn, srcs in cache.items()}
    for result in newly_scraped:
        if result.unit_price is not None:
            merged_cache.setdefault(result.part_number, {})[result.source] = result

    # 各部品の最安値を決定
    results: list[PriceResult] = []
    for part in parts:
        if part.manual_price is not None:
            results.append(manual_results[part.part_number])
            continue

        sources_to_try = _sources_for_part(part)
        candidates = [
            merged_cache[part.part_number][src]
            for src in sources_to_try
            if part.part_number in merged_cache
            and src in merged_cache[part.part_number]
            and merged_cache[part.part_number][src].unit_price is not None
        ]

        if candidates:
            results.append(min(candidates, key=lambda r: r.unit_price))
        else:
            results.append(PriceResult(
                part_number=part.part_number,
                unit_price=None,
                source="",
                error="全ての検索先で価格が見つかりませんでした",
            ))

    return results, newly_scraped


def _sources_for_part(part: Part) -> list[str]:
    """部品の仕入先希望から試すソースリストを返す"""
    source = part.preferred_source.lower().strip()
    if source and source in SCRAPERS:
        # 指定先 + フォールバック（指定先が失敗した場合に備える）
        return [source] + [s for s in DEFAULT_SOURCES if s != source]
    return DEFAULT_SOURCES


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

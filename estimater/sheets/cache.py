"""キャッシュシート: (型番, 仕入先) → 単価の保存・読み込み"""

from datetime import datetime
import gspread
from ..models import PriceResult
from .client import get_or_create_sheet

SHEET_NAME = "キャッシュ"
HEADERS = ["型番", "仕入先", "単価 (円)", "商品名", "取得URL", "取得日時"]

COL_PART_NUMBER = 0
COL_SOURCE = 1
COL_UNIT_PRICE = 2
COL_PRODUCT_NAME = 3
COL_URL = 4
COL_TIMESTAMP = 5


def load_cache(spreadsheet: gspread.Spreadsheet) -> dict[str, dict[str, PriceResult]]:
    """
    キャッシュシートを読み込む。
    戻り値: {型番: {仕入先: PriceResult}}
    """
    ws = get_or_create_sheet(spreadsheet, SHEET_NAME)
    all_values = ws.get_all_values()

    cache: dict[str, dict[str, PriceResult]] = {}
    for row in all_values[1:]:  # ヘッダーをスキップ
        if not row or not row[COL_PART_NUMBER]:
            continue
        part_number = row[COL_PART_NUMBER].strip()
        source = _get(row, COL_SOURCE)
        if not source:
            continue

        try:
            unit_price_str = _get(row, COL_UNIT_PRICE).replace(",", "")
            unit_price = float(unit_price_str) if unit_price_str else None
        except (ValueError, IndexError):
            unit_price = None

        result = PriceResult(
            part_number=part_number,
            unit_price=unit_price,
            source=source,
            product_name=_get(row, COL_PRODUCT_NAME),
            url=_get(row, COL_URL),
            from_cache=True,
        )
        cache.setdefault(part_number, {})[source] = result

    return cache


def save_cache(
    spreadsheet: gspread.Spreadsheet, results: list[PriceResult]
) -> None:
    """
    新しく取得した価格をキャッシュシートに書き込む。
    from_cache=True のもの (既存キャッシュ由来) はスキップする。
    同じ (型番, 仕入先) の既存行は上書きする。
    """
    ws = get_or_create_sheet(spreadsheet, SHEET_NAME)
    existing = ws.get_all_values()

    # 既存の (型番, 仕入先) → 行番号マップ (1始まり, ヘッダー行=1)
    existing_map: dict[tuple[str, str], int] = {}
    for i, row in enumerate(existing[1:], start=2):
        if row and _get(row, COL_PART_NUMBER) and _get(row, COL_SOURCE):
            key = (_get(row, COL_PART_NUMBER), _get(row, COL_SOURCE))
            existing_map[key] = i

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    new_rows: list[list] = []

    for result in results:
        if result.from_cache:
            continue  # キャッシュ由来はスキップ
        if result.unit_price is None:
            continue  # 取得失敗はキャッシュしない
        if not result.source:
            continue

        row_data = [
            result.part_number,
            result.source,
            f"{result.unit_price:,.0f}",
            result.product_name or "",
            result.url or "",
            now,
        ]

        key = (result.part_number, result.source)
        if key in existing_map:
            row_idx = existing_map[key]
            ws.update(f"A{row_idx}:F{row_idx}", [row_data])
        else:
            new_rows.append(row_data)

    if not existing or not existing[0]:
        ws.update("A1:F1", [HEADERS])

    if new_rows:
        next_row = len(existing) + 1
        ws.update(f"A{next_row}:F{next_row + len(new_rows) - 1}", new_rows)


def clear_cache(spreadsheet: gspread.Spreadsheet) -> int:
    """キャッシュシートをクリアする。削除件数を返す。"""
    ws = get_or_create_sheet(spreadsheet, SHEET_NAME)
    all_values = ws.get_all_values()
    count = max(0, len(all_values) - 1)
    ws.clear()
    ws.update("A1:F1", [HEADERS])
    return count


def _get(row: list[str], col: int) -> str:
    try:
        return row[col].strip()
    except IndexError:
        return ""

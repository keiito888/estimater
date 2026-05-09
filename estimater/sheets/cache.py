"""キャッシュシート: 型番→単価の保存・読み込み"""

from datetime import datetime
import gspread
from ..models import PriceResult
from .client import get_or_create_sheet

SHEET_NAME = "キャッシュ"
HEADERS = ["型番", "単価 (円)", "商品名", "仕入先", "取得URL", "取得日時"]

COL_PART_NUMBER = 0
COL_UNIT_PRICE = 1
COL_PRODUCT_NAME = 2
COL_SOURCE = 3
COL_URL = 4
COL_TIMESTAMP = 5


def load_cache(spreadsheet: gspread.Spreadsheet) -> dict[str, PriceResult]:
    """キャッシュシートから型番→PriceResult の辞書を読み込む"""
    ws = get_or_create_sheet(spreadsheet, SHEET_NAME)
    all_values = ws.get_all_values()

    cache: dict[str, PriceResult] = {}
    for row in all_values[1:]:  # ヘッダーをスキップ
        if not row or not row[COL_PART_NUMBER]:
            continue
        part_number = row[COL_PART_NUMBER].strip()
        try:
            unit_price_str = row[COL_UNIT_PRICE].replace(",", "").strip()
            unit_price = float(unit_price_str) if unit_price_str else None
        except (ValueError, IndexError):
            unit_price = None

        cache[part_number] = PriceResult(
            part_number=part_number,
            unit_price=unit_price,
            source=_get(row, COL_SOURCE) or "cache",
            product_name=_get(row, COL_PRODUCT_NAME),
            url=_get(row, COL_URL),
        )

    return cache


def save_cache(
    spreadsheet: gspread.Spreadsheet, results: list[PriceResult]
) -> None:
    """新しく取得した価格をキャッシュシートに書き込む (既存エントリは上書き)"""
    ws = get_or_create_sheet(spreadsheet, SHEET_NAME)
    existing = ws.get_all_values()

    # 既存の型番→行番号のマップ (1始まり、ヘッダー行=1)
    existing_map: dict[str, int] = {}
    for i, row in enumerate(existing[1:], start=2):
        if row and row[COL_PART_NUMBER]:
            existing_map[row[COL_PART_NUMBER].strip()] = i

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    new_rows: list[list] = []

    for result in results:
        if result.source == "cache":
            continue  # キャッシュから取得したものは再保存しない
        if result.unit_price is None:
            continue  # 取得失敗はキャッシュしない

        row_data = [
            result.part_number,
            f"{result.unit_price:,.0f}",
            result.product_name or "",
            result.source or "",
            result.url or "",
            now,
        ]

        if result.part_number in existing_map:
            # 既存行を更新
            row_idx = existing_map[result.part_number]
            ws.update(f"A{row_idx}:F{row_idx}", [row_data])
        else:
            new_rows.append(row_data)

    if not existing or not existing[0]:
        # ヘッダー行を作成
        ws.update("A1:F1", [HEADERS])

    if new_rows:
        next_row = len(existing) + 1
        ws.update(f"A{next_row}:F{next_row + len(new_rows) - 1}", new_rows)


def clear_cache(spreadsheet: gspread.Spreadsheet) -> int:
    """キャッシュシートをクリアする。削除件数を返す。"""
    ws = get_or_create_sheet(spreadsheet, SHEET_NAME)
    all_values = ws.get_all_values()
    count = max(0, len(all_values) - 1)  # ヘッダー除く
    ws.clear()
    ws.update("A1:F1", [HEADERS])
    return count


def _get(row: list[str], col: int) -> str:
    try:
        return row[col].strip()
    except IndexError:
        return ""

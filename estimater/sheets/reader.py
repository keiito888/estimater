"""入力シートから部品リストを読み込む"""

from typing import Optional
import gspread
from ..models import Part, PriceResult
from ..utils.infer import infer_maker, infer_category

SHEET_NAME = "入力"
HEADER_ROW = 1
DATA_START_ROW = 2

# ヘッダー列マッピング (0始まり)
COL_CATEGORY = 0        # 部品種別
COL_MAKER = 1           # メーカー
COL_PART_NUMBER = 2     # 型番
COL_QUANTITY = 3        # 数量
COL_PREFERRED = 4       # 仕入先希望
COL_NOTE = 5            # 備考
COL_MANUAL_PRICE = 6    # 手動単価 (入力済みならスクレイピングをスキップ)


def read_parts(spreadsheet: gspread.Spreadsheet) -> list[Part]:
    """入力シートから部品リストを読み込む"""
    ws = spreadsheet.worksheet(SHEET_NAME)
    all_values = ws.get_all_values()

    if len(all_values) < DATA_START_ROW:
        return []

    parts: list[Part] = []
    for row in all_values[DATA_START_ROW - 1:]:
        # 空行スキップ
        if not any(row):
            continue

        part_number = _get(row, COL_PART_NUMBER)
        if not part_number:
            continue

        try:
            quantity = int(_get(row, COL_QUANTITY) or "1")
        except ValueError:
            quantity = 1

        manual_price_str = _get(row, COL_MANUAL_PRICE).replace(",", "").replace("¥", "").replace("￥", "").strip()
        try:
            manual_price = float(manual_price_str) if manual_price_str else None
        except ValueError:
            manual_price = None

        parts.append(
            Part(
                category=_get(row, COL_CATEGORY),
                maker=_get(row, COL_MAKER),
                part_number=part_number,
                quantity=quantity,
                preferred_source=_get(row, COL_PREFERRED),
                note=_get(row, COL_NOTE),
                manual_price=manual_price,
            )
        )

    return parts


def ensure_input_sheet(spreadsheet: gspread.Spreadsheet) -> None:
    """入力シートが存在しない場合に作成してヘッダーを設定する"""
    try:
        spreadsheet.worksheet(SHEET_NAME)
    except gspread.WorksheetNotFound:
        ws = spreadsheet.add_worksheet(title=SHEET_NAME, rows=1000, cols=10)
        ws.update(
            "A1:G1",
            [["部品種別", "メーカー", "型番", "数量", "仕入先希望 (monotaro/rs/amazon/digikey/trusco/misumi)", "備考", "手動単価 (円)"]],
        )
        # サンプルデータ
        ws.update(
            "A2:G4",
            [
                ["遮断器", "三菱電機", "NF30-CS 3P 5A", "2", "misumi", "主幹", ""],
                ["電磁接触器", "富士電機", "SC-N1", "4", "monotaro", "", ""],
                ["端子台", "", "MKDS 1.5/2", "20", "", "", ""],
            ],
        )


def write_back_part_info(
    spreadsheet: gspread.Spreadsheet,
    parts: list[Part],
    results: list[PriceResult],
) -> int:
    """
    価格取得結果から推定したメーカー・部品種別を入力シートの空欄に書き戻す。
    既存の値は上書きしない。更新した件数を返す。
    """
    ws = spreadsheet.worksheet(SHEET_NAME)
    all_values = ws.get_all_values()
    updated = 0

    for i, (part, result) in enumerate(zip(parts, results)):
        if result.product_name is None:
            continue

        row_idx = DATA_START_ROW - 1 + i  # 0-based
        if row_idx >= len(all_values):
            continue

        row = all_values[row_idx]

        updates: list[tuple[str, str]] = []

        # メーカーが空欄の場合だけ補完
        current_maker = _get(row, COL_MAKER)
        if not current_maker:
            inferred = infer_maker(result.product_name)
            if inferred:
                cell = f"{_col_letter(COL_MAKER)}{row_idx + 1}"
                updates.append((cell, inferred))

        # 部品種別が空欄の場合だけ補完
        current_category = _get(row, COL_CATEGORY)
        if not current_category:
            inferred = infer_category(result.product_name)
            if inferred:
                cell = f"{_col_letter(COL_CATEGORY)}{row_idx + 1}"
                updates.append((cell, inferred))

        for cell, value in updates:
            ws.update([[value]], cell)
            updated += 1

    return updated


def _col_letter(col: int) -> str:
    """0始まりの列番号 → Excel列文字 (A, B, ...)"""
    letters = ""
    col += 1
    while col > 0:
        col, remainder = divmod(col - 1, 26)
        letters = chr(65 + remainder) + letters
    return letters


def _get(row: list[str], col: int) -> str:
    try:
        return row[col].strip()
    except IndexError:
        return ""

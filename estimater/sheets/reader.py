"""入力シートから部品リストを読み込む"""

import gspread
from ..models import Part

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

        parts.append(
            Part(
                category=_get(row, COL_CATEGORY),
                maker=_get(row, COL_MAKER),
                part_number=part_number,
                quantity=quantity,
                preferred_source=_get(row, COL_PREFERRED),
                note=_get(row, COL_NOTE),
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
            "A1:F1",
            [["部品種別", "メーカー", "型番", "数量", "仕入先希望 (misumi/monotaro)", "備考"]],
        )
        # サンプルデータ
        ws.update(
            "A2:F4",
            [
                ["遮断器", "三菱電機", "NF30-CS 3P 5A", "2", "misumi", "主幹"],
                ["電磁接触器", "富士電機", "SC-N1", "4", "monotaro", ""],
                ["端子台", "", "MKDS 1.5/2", "20", "", ""],
            ],
        )


def _get(row: list[str], col: int) -> str:
    try:
        return row[col].strip()
    except IndexError:
        return ""

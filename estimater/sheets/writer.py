"""見積書シートへの書き込み"""

from datetime import date
import gspread
from gspread.utils import rowcol_to_a1
from ..models import QuoteItem
from .client import get_or_create_sheet

SHEET_NAME = "見積書"

# 列定義
COLS = ["No", "部品種別", "メーカー", "型番", "数量", "単価 (円)", "小計 (円)", "仕入先", "備考", "状態"]


def write_quote(
    spreadsheet: gspread.Spreadsheet,
    items: list[QuoteItem],
    company_name: str = "",
    tax_rate: float = 0.10,
) -> None:
    """見積書シートに結果を書き込む"""
    ws = get_or_create_sheet(spreadsheet, SHEET_NAME)
    ws.clear()

    today = date.today().strftime("%Y年%m月%d日")
    rows: list[list] = []

    # ヘッダーブロック
    rows.append([f"御見積書", "", "", "", "", "", "", "", "", ""])
    rows.append(["", "", "", "", "", "作成日:", today, "", "", ""])
    if company_name:
        rows.append(["作成者:", company_name, "", "", "", "", "", "", "", ""])
    rows.append([])  # 空行

    # 列ヘッダー
    rows.append(COLS)

    # 明細行
    subtotal_sum = 0.0
    for item in items:
        unit_price = item.price_result.unit_price
        subtotal = item.subtotal

        if subtotal is not None:
            subtotal_sum += subtotal

        rows.append([
            item.row_num,
            item.part.category,
            item.part.maker,
            item.part.part_number,
            item.part.quantity,
            f"{unit_price:,.0f}" if unit_price is not None else "要確認",
            f"{subtotal:,.0f}" if subtotal is not None else "要確認",
            item.price_result.source or "",
            item.part.note,
            "OK" if unit_price is not None else "価格取得失敗",
        ])

    # 合計行
    rows.append([])
    rows.append(["", "", "", "", "", "小計", f"{subtotal_sum:,.0f}", "", "", ""])

    tax = subtotal_sum * tax_rate
    rows.append(["", "", "", "", "", f"消費税 ({int(tax_rate * 100)}%)", f"{tax:,.0f}", "", "", ""])
    rows.append(["", "", "", "", "", "合計 (税込)", f"{subtotal_sum + tax:,.0f}", "", "", ""])

    ws.update("A1", rows)

    # 列ヘッダー行を太字に
    header_row = 5 if not company_name else 6
    ws.format(f"A{header_row}:J{header_row}", {"textFormat": {"bold": True}})

    # タイトル行を大きく
    ws.format("A1", {"textFormat": {"bold": True, "fontSize": 14}})

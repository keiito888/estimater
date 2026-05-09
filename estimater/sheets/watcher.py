"""スプレッドシートのトリガーセルを監視・操作する"""

import gspread
from .client import get_or_create_sheet

TRIGGER_SHEET = "制御"
TRIGGER_CELL = "B2"     # ステータスセル
BUTTON_LABEL_CELL = "A2"


def get_trigger_status(spreadsheet: gspread.Spreadsheet) -> str:
    """トリガーセルの値を返す"""
    try:
        ws = spreadsheet.worksheet(TRIGGER_SHEET)
        return ws.acell(TRIGGER_CELL).value or ""
    except gspread.WorksheetNotFound:
        return ""


def set_trigger_status(spreadsheet: gspread.Spreadsheet, status: str) -> None:
    """トリガーセルの値を更新する"""
    ws = get_or_create_sheet(spreadsheet, TRIGGER_SHEET)
    ws.update(TRIGGER_CELL, status)


def setup_control_sheet(spreadsheet: gspread.Spreadsheet) -> str:
    """
    「制御」シートを作成し、GASスクリプトのコードを返す。
    ユーザーがこのGASコードをスクリプトエディタに貼り付けることで
    シート上にボタンが設置される。
    """
    ws = get_or_create_sheet(spreadsheet, TRIGGER_SHEET)
    ws.clear()

    # レイアウト設定
    ws.update([["部品見積もりツール 実行コントロール", "", ""]], "A1:C1")
    ws.update([["▼ 上部メニュー「見積もりツール」から実行", "待機中", ""]], "A2:C2")
    ws.update([["※ Pythonスクリプトが実行中である必要があります"]], "A4")
    ws.update([["  py -m estimater watch"]], "A5")

    # 書式設定
    ws.format("A1:C1", {
        "textFormat": {"bold": True, "fontSize": 14},
        "backgroundColor": {"red": 0.2, "green": 0.4, "blue": 0.8},
    })
    ws.format(TRIGGER_CELL, {
        "textFormat": {"bold": True},
        "horizontalAlignment": "CENTER",
    })

    # GASコードを生成して返す
    sheet_id = spreadsheet.id
    gas_code = f'''// このスクリプトをスプレッドシートのスクリプトエディタに貼り付けてください
// 拡張機能 > Apps Script > このコードを貼り付けて保存 > 実行ボタンを設置

function runEstimation() {{
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var ws = ss.getSheetByName("{TRIGGER_SHEET}");
  if (!ws) {{
    SpreadsheetApp.getUi().alert('「{TRIGGER_SHEET}」シートが見つかりません。\\npy -m estimater setup を実行してください。');
    return;
  }}
  ws.getRange("{TRIGGER_CELL}").setValue("RUN");
  SpreadsheetApp.getUi().alert("見積もり実行を開始します。\\nPythonスクリプト（py -m estimater watch）が実行中であることを確認してください。");
}}

function onOpen() {{
  SpreadsheetApp.getUi()
    .createMenu("見積もりツール")
    .addItem("▶ 見積もりを実行する", "runEstimation")
    .addToUi();
}}
'''
    return gas_code

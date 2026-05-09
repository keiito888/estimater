"""スプレッドシートの初期セットアップ (シート作成・設定シート)"""

import gspread
from .client import get_or_create_sheet
from .reader import ensure_input_sheet
from .cache import SHEET_NAME as CACHE_SHEET, HEADERS as CACHE_HEADERS


def setup_spreadsheet(spreadsheet: gspread.Spreadsheet) -> None:
    """必要な全シートを作成・初期化する"""
    ensure_input_sheet(spreadsheet)
    _setup_cache_sheet(spreadsheet)
    _setup_settings_sheet(spreadsheet)
    _setup_quote_sheet(spreadsheet)


def _setup_cache_sheet(spreadsheet: gspread.Spreadsheet) -> None:
    ws = get_or_create_sheet(spreadsheet, CACHE_SHEET)
    existing = ws.get_all_values()
    if not existing or not existing[0]:
        ws.update("A1:F1", [CACHE_HEADERS])


def _setup_settings_sheet(spreadsheet: gspread.Spreadsheet) -> None:
    ws = get_or_create_sheet(spreadsheet, "設定")
    existing = ws.get_all_values()
    if not existing or not existing[0]:
        ws.update(
            "A1:B6",
            [
                ["設定項目", "値"],
                ["自社名", "株式会社〇〇"],
                ["担当者名", ""],
                ["消費税率", "0.10"],
                ["有効期限 (日数)", "30"],
                ["備考欄デフォルト文", ""],
            ],
        )


def _setup_quote_sheet(spreadsheet: gspread.Spreadsheet) -> None:
    get_or_create_sheet(spreadsheet, "見積書")


def read_settings(spreadsheet: gspread.Spreadsheet) -> dict[str, str]:
    """設定シートからキー・バリューを読み込む"""
    try:
        ws = spreadsheet.worksheet("設定")
    except gspread.WorksheetNotFound:
        return {}

    all_values = ws.get_all_values()
    settings: dict[str, str] = {}
    for row in all_values[1:]:  # ヘッダー除く
        if len(row) >= 2 and row[0]:
            settings[row[0].strip()] = row[1].strip()
    return settings

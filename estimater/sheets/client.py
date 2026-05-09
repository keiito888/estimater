"""Google Sheets クライアントの初期化"""

import gspread
from google.oauth2.service_account import Credentials
from ..config import get_credentials_path

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]


def get_client() -> gspread.Client:
    creds = Credentials.from_service_account_file(
        str(get_credentials_path()), scopes=SCOPES
    )
    return gspread.authorize(creds)


def get_spreadsheet(spreadsheet_id: str) -> gspread.Spreadsheet:
    client = get_client()
    return client.open_by_key(spreadsheet_id)


def get_or_create_sheet(
    spreadsheet: gspread.Spreadsheet, title: str
) -> gspread.Worksheet:
    """シートを取得。存在しない場合は作成する。"""
    try:
        return spreadsheet.worksheet(title)
    except gspread.WorksheetNotFound:
        return spreadsheet.add_worksheet(title=title, rows=1000, cols=20)

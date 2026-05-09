"""Slack Incoming Webhook で見積もり完了を通知する"""

import os
from typing import Optional
import requests

from ..config import _PROJECT_ROOT
from dotenv import load_dotenv

load_dotenv(_PROJECT_ROOT / ".env")


def _webhook_url() -> Optional[str]:
    return os.getenv("SLACK_WEBHOOK_URL") or None


def _channel() -> Optional[str]:
    return os.getenv("SLACK_CHANNEL") or None


def is_enabled() -> bool:
    return bool(_webhook_url())


def notify_complete(
    ok_count: int,
    ng_count: int,
    total_price: float,
    spreadsheet_id: str,
    filled_count: int = 0,
) -> bool:
    """
    見積もり完了を Slack に通知する。
    成功した場合は True、設定なし or 失敗の場合は False を返す。
    """
    url = _webhook_url()
    if not url:
        return False

    sheet_url = f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/edit"
    status_emoji = ":white_check_mark:" if ng_count == 0 else ":warning:"
    total_str = f"{total_price:,.0f}" if total_price else "—"

    lines = [
        f"{status_emoji} *見積もりが完了しました*",
        "",
        f"- 取得成功: *{ok_count} 件*",
    ]
    if ng_count:
        lines.append(f"- 要確認 (価格未取得): *{ng_count} 件*")
    if filled_count:
        lines.append(f"- 自動補完 (メーカー・品名): {filled_count} セル")
    lines += [
        f"- 合計金額 (税抜): *¥{total_str}*",
        "",
        f"[見積書を開く]({sheet_url})",
    ]

    payload: dict = {"text": "\n".join(lines)}
    channel = _channel()
    if channel:
        payload["channel"] = channel

    try:
        resp = requests.post(url, json=payload, timeout=10)
        return resp.status_code == 200
    except Exception:
        return False


def notify_error(error_message: str, spreadsheet_id: str = "") -> bool:
    """見積もり中のエラーを Slack に通知する"""
    url = _webhook_url()
    if not url:
        return False

    lines = [
        ":x: *見積もりでエラーが発生しました*",
        "",
        f"> {error_message}",
    ]
    if spreadsheet_id:
        sheet_url = f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/edit"
        lines.append(f"\n[スプレッドシートを開く]({sheet_url})")

    payload: dict = {"text": "\n".join(lines)}
    channel = _channel()
    if channel:
        payload["channel"] = channel

    try:
        resp = requests.post(url, json=payload, timeout=10)
        return resp.status_code == 200
    except Exception:
        return False

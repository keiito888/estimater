"""Mouser Electronics API v1 から型番で価格を取得するスクレイパー

環境変数:
    MOUSER_API_KEY - mouser.jp の My Account → APIs → Manage で発行した Search API キー

未設定の場合は「設定なし」エラーを返す（Playwrightは使用しない）。
"""

import os
import re
from typing import Optional
from playwright.sync_api import Page

import requests

from ..models import PriceResult
from ..config import _PROJECT_ROOT
from dotenv import load_dotenv

load_dotenv(_PROJECT_ROOT / ".env")

SEARCH_URL = "https://api.mouser.com/api/v1/search/partnumber"


def fetch_price(page: Page, part_number: str) -> PriceResult:
    """
    Mouser API v1 で型番を検索し、単価を返す。
    page 引数は使用しない（API呼び出しのみ）。
    """
    api_key = os.getenv("MOUSER_API_KEY", "")
    if not api_key:
        return PriceResult(
            part_number=part_number,
            unit_price=None,
            source="mouser",
            error="MOUSER_API_KEY が未設定です",
        )

    try:
        resp = requests.post(
            f"{SEARCH_URL}?apiKey={api_key}",
            headers={"Content-Type": "application/json", "Accept": "application/json"},
            json={
                "SearchByPartRequest": {
                    "mouserPartNumber": part_number,
                    "partSearchOptions": "Contains",
                }
            },
            timeout=15,
        )

        if resp.status_code != 200:
            return PriceResult(
                part_number=part_number,
                unit_price=None,
                source="mouser",
                error=f"APIエラー: HTTP {resp.status_code}",
            )

        data = resp.json()
        errors = data.get("Errors") or []
        if errors:
            return PriceResult(
                part_number=part_number,
                unit_price=None,
                source="mouser",
                error=str(errors[0]),
            )

        parts = (data.get("SearchResults") or {}).get("Parts") or []
        if not parts:
            return PriceResult(
                part_number=part_number,
                unit_price=None,
                source="mouser",
                error="商品が見つかりませんでした",
            )

        product = parts[0]
        unit_price, currency = _extract_price(product)
        product_url = product.get("ProductDetailUrl") or ""
        product_name = _build_product_name(product)

        error = None
        if unit_price is None:
            error = "価格が見つかりませんでした"
        elif currency and currency.upper() not in ("JPY", "¥", ""):
            # 外貨表示の場合は警告を付ける
            error = f"価格は {currency} 建てです (JPY換算が必要な場合は手動単価を入力してください)"

        return PriceResult(
            part_number=part_number,
            unit_price=unit_price,
            source="mouser",
            product_name=product_name,
            url=product_url,
            error=error,
        )

    except Exception as e:
        return PriceResult(
            part_number=part_number, unit_price=None, source="mouser", error=str(e)
        )


def _extract_price(product: dict) -> tuple[Optional[float], str]:
    """PriceBreaks から1個当たりの単価と通貨を返す"""
    price_breaks = product.get("PriceBreaks") or []
    for tier in price_breaks:
        qty = tier.get("Quantity") or 0
        if int(qty) == 1:
            return _parse_price_str(tier.get("Price", "")), tier.get("Currency", "")

    # 数量1がなければ最初のティア
    if price_breaks:
        tier = price_breaks[0]
        return _parse_price_str(tier.get("Price", "")), tier.get("Currency", "")

    return None, ""


def _parse_price_str(price_str: str) -> Optional[float]:
    """'¥1,234' や '$0.10' などの価格文字列を float に変換"""
    cleaned = re.sub(r"[^\d.]", "", str(price_str))
    try:
        val = float(cleaned) if cleaned else None
        return val if val and val > 0 else None
    except ValueError:
        return None


def _build_product_name(product: dict) -> str:
    parts = []
    if product.get("Manufacturer"):
        parts.append(product["Manufacturer"])
    if product.get("Description"):
        parts.append(product["Description"])
    return " ".join(parts) if parts else (product.get("ManufacturerPartNumber") or "")

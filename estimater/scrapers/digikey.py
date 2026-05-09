"""Digi-Key API v4 から型番で価格を取得するスクレイパー

環境変数:
    DIGIKEY_CLIENT_ID     - developer.digikey.com で発行した Client ID
    DIGIKEY_CLIENT_SECRET - 同 Client Secret

未設定の場合は「設定なし」エラーを返す（Playwrightは使用しない）。
"""

import os
import time
import re
from typing import Optional
from playwright.sync_api import Page

import requests

from ..models import PriceResult
from ..config import _PROJECT_ROOT
from dotenv import load_dotenv

load_dotenv(_PROJECT_ROOT / ".env")

TOKEN_URL   = "https://api.digikey.com/v1/oauth2/token"
SEARCH_URL  = "https://api.digikey.com/products/v4/search/keyword"

# インメモリトークンキャッシュ
_token_cache: dict = {"access_token": None, "expires_at": 0.0}


def _get_token() -> Optional[str]:
    """Client Credentials フローでアクセストークンを取得（10分キャッシュ）"""
    now = time.time()
    if _token_cache["access_token"] and now < _token_cache["expires_at"] - 30:
        return _token_cache["access_token"]

    client_id     = os.getenv("DIGIKEY_CLIENT_ID", "")
    client_secret = os.getenv("DIGIKEY_CLIENT_SECRET", "")
    if not client_id or not client_secret:
        return None

    resp = requests.post(
        TOKEN_URL,
        data={
            "client_id":     client_id,
            "client_secret": client_secret,
            "grant_type":    "client_credentials",
        },
        timeout=15,
    )
    if resp.status_code != 200:
        return None

    data = resp.json()
    _token_cache["access_token"] = data.get("access_token")
    _token_cache["expires_at"]   = now + int(data.get("expires_in", 599))
    return _token_cache["access_token"]


def fetch_price(page: Page, part_number: str) -> PriceResult:
    """
    Digi-Key API v4 で型番を検索し、単価を返す。
    page 引数は使用しない（API呼び出しのみ）。
    """
    client_id = os.getenv("DIGIKEY_CLIENT_ID", "")
    if not client_id:
        return PriceResult(
            part_number=part_number,
            unit_price=None,
            source="digikey",
            error="DIGIKEY_CLIENT_ID / DIGIKEY_CLIENT_SECRET が未設定です",
        )

    token = _get_token()
    if not token:
        return PriceResult(
            part_number=part_number,
            unit_price=None,
            source="digikey",
            error="Digi-Key APIトークンの取得に失敗しました",
        )

    try:
        resp = requests.post(
            SEARCH_URL,
            headers={
                "X-DIGIKEY-Client-Id":        client_id,
                "Authorization":              f"Bearer {token}",
                "X-DIGIKEY-Locale-Site":      "JP",
                "X-DIGIKEY-Locale-Language":  "ja",
                "X-DIGIKEY-Locale-Currency":  "JPY",
                "Content-Type":               "application/json",
                "Accept":                     "application/json",
            },
            json={"Keywords": part_number, "Limit": 5},
            timeout=15,
        )

        if resp.status_code != 200:
            return PriceResult(
                part_number=part_number,
                unit_price=None,
                source="digikey",
                error=f"APIエラー: HTTP {resp.status_code}",
            )

        data = resp.json()
        products = data.get("Products") or []

        if not products:
            return PriceResult(
                part_number=part_number,
                unit_price=None,
                source="digikey",
                error="商品が見つかりませんでした",
            )

        # 最初の商品の価格を取得
        product     = products[0]
        unit_price  = _extract_price(product)
        product_url = product.get("ProductUrl") or ""
        product_name = _build_product_name(product)

        return PriceResult(
            part_number=part_number,
            unit_price=unit_price,
            source="digikey",
            product_name=product_name,
            url=product_url,
            error=None if unit_price else "価格が見つかりませんでした",
        )

    except Exception as e:
        return PriceResult(
            part_number=part_number,
            unit_price=None,
            source="digikey",
            error=str(e),
        )


def _extract_price(product: dict) -> Optional[float]:
    """APIレスポンスから単価を取得する"""
    # UnitPrice フィールド (数値型)
    unit_price = product.get("UnitPrice")
    if unit_price is not None:
        try:
            val = float(unit_price)
            if val > 0:
                return val
        except (ValueError, TypeError):
            pass

    # PricingTiers から 1個単価を取得
    tiers = product.get("PricingTiers") or []
    for tier in tiers:
        if tier.get("BreakQuantity") == 1:
            price = tier.get("UnitPrice") or tier.get("TotalPrice")
            if price:
                try:
                    val = float(price)
                    if val > 0:
                        return val
                except (ValueError, TypeError):
                    pass

    # 最初のティアの価格
    if tiers:
        price = tiers[0].get("UnitPrice") or tiers[0].get("TotalPrice")
        if price:
            try:
                val = float(price)
                if val > 0:
                    return val
            except (ValueError, TypeError):
                pass

    return None


def _build_product_name(product: dict) -> str:
    """商品名文字列を組み立てる"""
    parts = []
    manufacturer = (product.get("Manufacturer") or {}).get("Name", "")
    if manufacturer:
        parts.append(manufacturer)
    description = product.get("ProductDescription") or ""
    if description:
        parts.append(description)
    return " ".join(parts) if parts else (product.get("ManufacturerPartNumber") or "")

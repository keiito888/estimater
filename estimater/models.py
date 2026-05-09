"""データモデル定義"""

from dataclasses import dataclass, field
from typing import Literal, Optional


@dataclass
class Part:
    """入力シートの1行 = 1部品"""
    category: str           # 部品種別 (例: 遮断器)
    maker: str              # メーカー (例: 三菱電機)
    part_number: str        # 型番 (例: NF30-CS 3P 5A)
    quantity: int           # 数量
    preferred_source: str   # 仕入先希望 (misumi / monotaro / 空欄)
    note: str = ""          # 備考


@dataclass
class PriceResult:
    """価格取得結果"""
    part_number: str
    unit_price: Optional[float]         # 取得できなかった場合は None
    source: Optional[str]               # "misumi" / "monotaro" / "cache"
    product_name: Optional[str] = None  # サイト上の商品名
    url: Optional[str] = None           # 取得元URL
    error: Optional[str] = None         # エラーメッセージ


@dataclass
class QuoteItem:
    """見積書の1行"""
    row_num: int
    part: Part
    price_result: PriceResult

    @property
    def subtotal(self) -> Optional[float]:
        if self.price_result.unit_price is None:
            return None
        return self.price_result.unit_price * self.part.quantity

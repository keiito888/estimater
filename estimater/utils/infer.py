"""商品名からメーカー・部品種別を推定するユーティリティ"""

import re
from typing import Optional

# メーカー名のパターン: (表示名, 検索パターンのリスト)
_MAKER_PATTERNS: list[tuple[str, list[str]]] = [
    ("オムロン",      [r"omron", r"オムロン", r"OMRON"]),
    ("三菱電機",      [r"mitsubishi", r"三菱電機", r"三菱"]),
    ("富士電機",      [r"fuji electric", r"富士電機", r"富士"]),
    ("シュナイダー",  [r"schneider", r"シュナイダー"]),
    ("ABB",           [r"\bABB\b"]),
    ("IDEC",          [r"\bIDEC\b", r"アイデック"]),
    ("パナソニック",  [r"panasonic", r"パナソニック"]),
    ("春日電機",      [r"kasuga", r"春日電機"]),
    ("日東工業",      [r"nitto kogyo", r"日東工業"]),
    ("Eaton",         [r"\beaton\b"]),
    ("TE Connectivity", [r"te connectivity", r"tyco", r"amp\b"]),
    ("Phoenix Contact", [r"phoenix contact", r"フェニックス"]),
    ("Weidmuller",    [r"weidmuller", r"ワイドミュラー"]),
    ("WAGO",          [r"\bwago\b"]),
    ("シーメンス",    [r"siemens", r"シーメンス"]),
    ("キーエンス",    [r"keyence", r"キーエンス"]),
    ("SMC",           [r"\bSMC\b"]),
    ("CKD",           [r"\bCKD\b"]),
    ("TRUSCO",        [r"\bTRUSCO\b", r"トラスコ"]),
    ("日本電産",      [r"nidec", r"日本電産"]),
    ("SHARP",         [r"\bsharp\b", r"シャープ"]),
    ("COSEL",         [r"\bcosel\b", r"コーセル"]),
    ("TDK-Lambda",    [r"tdk.?lambda", r"tdk"]),
    ("明電舎",        [r"meidensha", r"明電舎"]),
]

# 部品種別のキーワード: (表示名, 検索キーワードのリスト)
_CATEGORY_PATTERNS: list[tuple[str, list[str]]] = [
    ("遮断器",        [r"遮断器", r"ブレーカ", r"breaker", r"\bNFB\b", r"\bMCCB\b"]),
    ("電磁接触器",    [r"電磁接触器", r"接触器", r"コンタクタ", r"contactor", r"magnetic switch"]),
    ("リレー",        [r"リレー", r"relay", r"ソリッドステート"]),
    ("タイマ",        [r"タイマ", r"timer"]),
    ("電源",          [r"電源", r"power supply", r"スイッチング電源"]),
    ("端子台",        [r"端子台", r"terminal block"]),
    ("センサ",        [r"センサ", r"sensor", r"検出器", r"フォトセンサ", r"近接"]),
    ("押しボタン",    [r"押しボタン", r"push button", r"操作スイッチ"]),
    ("表示灯",        [r"表示灯", r"パイロット", r"pilot lamp", r"indicator"]),
    ("変圧器",        [r"変圧器", r"トランス", r"transformer"]),
    ("配線ダクト",    [r"配線ダクト", r"ケーブルダクト"]),
    ("電線",          [r"電線", r"ケーブル", r"cable"]),
    ("漏電遮断器",    [r"漏電遮断器", r"漏電", r"\bELCB\b", r"\bRCCB\b"]),
    ("インバータ",    [r"インバータ", r"inverter", r"VFD", r"VSD"]),
    ("サーボ",        [r"サーボ", r"servo"]),
    ("PLC",           [r"\bPLC\b", r"プログラマブル", r"programmable controller"]),
    ("HMI",           [r"\bHMI\b", r"タッチパネル", r"表示器"]),
    ("ノイズフィルタ", [r"ノイズフィルタ", r"ラインフィルタ", r"EMC", r"EMI"]),
]


def infer_maker(product_name: str) -> Optional[str]:
    """商品名からメーカー名を推定する"""
    if not product_name:
        return None
    text = product_name.strip()
    for display_name, patterns in _MAKER_PATTERNS:
        for pat in patterns:
            if re.search(pat, text, re.IGNORECASE):
                return display_name
    return None


def infer_category(product_name: str) -> Optional[str]:
    """商品名から部品種別を推定する"""
    if not product_name:
        return None
    text = product_name.strip()
    for display_name, patterns in _CATEGORY_PATTERNS:
        for pat in patterns:
            if re.search(pat, text, re.IGNORECASE):
                return display_name
    return None


def infer_from_product_name(product_name: str) -> tuple[Optional[str], Optional[str]]:
    """商品名からメーカーと部品種別を返す (maker, category) のタプル"""
    return infer_maker(product_name), infer_category(product_name)

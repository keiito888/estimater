"""スクレイパー共通ユーティリティ"""


def part_number_in_page(part_number: str, page_text: str) -> bool:
    """
    ページテキストに型番（または主要トークン）が含まれているか確認する。
    大文字小文字は無視する。
    """
    key = part_number.strip().upper()
    text = page_text.upper()
    if key in text:
        return True
    # スペース区切りの最初のトークンだけでも一致すればOK
    first_token = key.split()[0] if key.split() else key
    return first_token in text

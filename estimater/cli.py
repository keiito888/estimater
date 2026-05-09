"""CLIエントリーポイント"""

from typing import Optional
import typer
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn

from .config import get_spreadsheet_id
from .models import QuoteItem
from .scrapers.engine import fetch_prices
from .sheets.client import get_spreadsheet
from .sheets.reader import read_parts
from .sheets.writer import write_quote
from .sheets.cache import load_cache, save_cache, clear_cache
from .sheets.setup import setup_spreadsheet, read_settings

app = typer.Typer(help="制御盤向け電気部品 自動見積もりツール")
console = Console()


@app.command()
def run(
    sheet_id: Optional[str] = typer.Option(
        None, "--sheet", "-s", help="スプレッドシートID (省略時は .env の SPREADSHEET_ID を使用)"
    ),
    no_cache: bool = typer.Option(False, "--no-cache", help="キャッシュを無視して再取得"),
    headless: bool = typer.Option(True, "--headless/--no-headless", help="ヘッドレスモード"),
) -> None:
    """入力シートを読み込み、価格を取得して見積書シートに書き込む"""
    import os
    if not headless:
        os.environ["HEADLESS"] = "false"

    spreadsheet_id = sheet_id or get_spreadsheet_id()

    with Progress(SpinnerColumn("line"), TextColumn("{task.description}"), console=console) as progress:
        task = progress.add_task("スプレッドシートに接続中...", total=None)
        spreadsheet = get_spreadsheet(spreadsheet_id)
        progress.update(task, description="スプレッドシートに接続しました")

        progress.update(task, description="設定を読み込んでいます...")
        settings = read_settings(spreadsheet)
        company_name = settings.get("自社名", "")
        tax_rate = float(settings.get("消費税率", "0.10"))

        progress.update(task, description="入力シートを読み込んでいます...")
        parts = read_parts(spreadsheet)

    if not parts:
        console.print("[yellow]入力シートに部品が見つかりません。型番を入力してから再実行してください。[/yellow]")
        raise typer.Exit(1)

    console.print(f"[green]✓[/green] {len(parts)} 件の部品を読み込みました")

    # キャッシュ読み込み
    cache: dict = {}
    if not no_cache:
        with Progress(SpinnerColumn("line"), TextColumn("{task.description}"), console=console) as progress:
            task = progress.add_task("キャッシュを読み込んでいます...", total=None)
            cache = load_cache(spreadsheet)
        cached_count = sum(1 for p in parts if p.part_number in cache)
        if cached_count:
            console.print(f"[cyan]キャッシュヒット: {cached_count} 件 (スクレイピングをスキップ)[/cyan]")

    # 価格取得
    uncached_count = sum(1 for p in parts if p.part_number not in cache)
    if uncached_count > 0:
        console.print(f"[bold]価格取得を開始します ({uncached_count} 件)...[/bold]")

    results = fetch_prices(parts, cache)

    # 結果表示
    _print_results_table(parts, results)

    # キャッシュ保存
    with Progress(SpinnerColumn("line"), TextColumn("{task.description}"), console=console) as progress:
        task = progress.add_task("キャッシュを保存しています...", total=None)
        save_cache(spreadsheet, results)

        # 見積書シートに書き込み
        progress.update(task, description="見積書シートに書き込んでいます...")
        items = [
            QuoteItem(row_num=i + 1, part=part, price_result=result)
            for i, (part, result) in enumerate(zip(parts, results))
        ]
        write_quote(spreadsheet, items, company_name=company_name, tax_rate=tax_rate)

    ok_count = sum(1 for r in results if r.unit_price is not None)
    ng_count = len(results) - ok_count
    console.print(f"\n[green]✓ 完了[/green]  成功: {ok_count} 件  ", end="")
    if ng_count:
        console.print(f"[red]要確認: {ng_count} 件[/red]")
    else:
        console.print("")
    console.print(f"スプレッドシートの「見積書」シートを確認してください。")
    console.print(f"URL: https://docs.google.com/spreadsheets/d/{spreadsheet_id}/edit")


@app.command()
def setup(
    sheet_id: Optional[str] = typer.Option(
        None, "--sheet", "-s", help="スプレッドシートID"
    ),
) -> None:
    """スプレッドシートの初期セットアップ (シート作成・サンプルデータ)"""
    spreadsheet_id = sheet_id or get_spreadsheet_id()

    with Progress(SpinnerColumn("line"), TextColumn("{task.description}"), console=console) as progress:
        task = progress.add_task("セットアップ中...", total=None)
        spreadsheet = get_spreadsheet(spreadsheet_id)
        progress.update(task, description="シートを作成しています...")
        setup_spreadsheet(spreadsheet)

    console.print("[green]✓ セットアップ完了[/green]")
    console.print("「入力」シートに部品情報を入力してから [bold]estimater run[/bold] を実行してください。")


@app.command()
def login(
    site: str = typer.Argument("misumi", help="ログインするサイト: misumi または monotaro"),
) -> None:
    """ブラウザを開いてサイトにログインし、セッションを保存する"""
    from playwright.sync_api import sync_playwright
    from .scrapers.session import (
        MISUMI_LOGIN_URL, save_misumi_session, MISUMI_SESSION_FILE
    )

    site = site.lower().strip()
    if site not in ("misumi", "monotaro"):
        console.print(f"[red]エラー: サイトは 'misumi' または 'monotaro' を指定してください[/red]")
        raise typer.Exit(1)

    login_url = MISUMI_LOGIN_URL if site == "misumi" else "https://www.monotaro.com/login.html"

    console.print(f"[bold]ブラウザを開きます。{site} にログインしてください。[/bold]")
    console.print("ログイン完了後、ブラウザを閉じると自動的にセッションが保存されます。")
    console.print(f"ログインURL: {login_url}\n")

    with sync_playwright() as pw:
        browser = pw.firefox.launch(headless=False)
        context = browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:126.0) "
                "Gecko/20100101 Firefox/126.0"
            ),
            locale="ja-JP",
            viewport={"width": 1280, "height": 800},
        )
        page = context.new_page()
        page.goto(login_url)

        console.print("[yellow]ブラウザでログインしてください。完了したら Enter を押してください...[/yellow]")
        input()

        # セッション（Cookie）を保存
        storage = context.storage_state()
        if site == "misumi":
            save_misumi_session(storage)
            console.print(f"[green]✓ Misumiセッションを保存しました: {MISUMI_SESSION_FILE}[/green]")
        browser.close()

    console.print("次回から py -m estimater run を実行するとログイン済み状態でスクレイピングします。")


@app.command()
def cache_clear(
    sheet_id: Optional[str] = typer.Option(
        None, "--sheet", "-s", help="スプレッドシートID"
    ),
) -> None:
    """キャッシュシートをクリアする"""
    spreadsheet_id = sheet_id or get_spreadsheet_id()
    spreadsheet = get_spreadsheet(spreadsheet_id)
    count = clear_cache(spreadsheet)
    console.print(f"[green]✓[/green] キャッシュを {count} 件削除しました")


def _print_results_table(parts, results) -> None:
    table = Table(title="価格取得結果", show_lines=True)
    table.add_column("型番", style="cyan")
    table.add_column("単価 (円)", justify="right")
    table.add_column("仕入先")
    table.add_column("状態")

    for part, result in zip(parts, results):
        if result.unit_price is not None:
            price_str = f"{result.unit_price:,.0f}"
            status = "[green]OK[/green]"
        else:
            price_str = "-"
            status = f"[red]失敗: {result.error or '不明'}[/red]"

        table.add_row(
            part.part_number,
            price_str,
            result.source or "",
            status,
        )

    console.print(table)


if __name__ == "__main__":
    app()

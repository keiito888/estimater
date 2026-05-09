@echo off
chcp 65001 > nul
title 見積もりツール（監視モード）
cd /d "%~dp0"
echo ==========================================
echo   部品見積もりツール 監視モード
echo   スプレッドシートのボタンを押すと
echo   自動で見積もりが実行されます
echo   停止: Ctrl+C
echo ==========================================
echo.
set PYTHONUTF8=1
py -m estimater watch
pause > nul

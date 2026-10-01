@echo off
chcp 65001 >nul
REM 本机(国内IP)一键更新三个RSS并推送到GitHub + 刷新jsDelivr
REM 双击运行即可；首次使用请先确认 rmrp-rss 文件夹是 git 仓库（见下方说明）
set "PY=C:\Users\Lee\.workbuddy\binaries\python\versions\3.13.12\python.exe"
if not exist "%PY%" set "PY=python"
cd /d "%~dp0"
"%PY%" update_and_push.py
echo.
echo 按任意键关闭窗口...
pause >nul

@echo off
setlocal
cd /d "%~dp0"
set PY=C:\Users\Lee\.workbuddy\binaries\python\versions\3.13.12\python.exe
if not exist "%PY%" set PY=python
echo 正在生成本机(国内IP)更新并推送到 GitHub，请稍候...
"%PY%" update_and_push.py
echo.
echo 若上方出现用户名/密码提示，用户名填 GitHub 账号，密码填 Token（不是登录密码）。
echo 输入 exit 并回车可关闭此窗口。
cmd /k

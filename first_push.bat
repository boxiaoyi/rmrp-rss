@echo off
chcp 65001 >nul
REM 首次上传用：把本机已整理好的仓库推到 GitHub（只推送，不再生成，保护已有好内容）
REM 双击运行即可。若提示输入用户名/密码，用户名填 GitHub 账号，密码填 Personal Access Token（不是登录密码）。
cd /d "%~dp0"
git fetch origin main
git merge --allow-unrelated-histories -X ours origin/main
git push -u origin main
echo.
echo 完成。若上方出现用户名/密码提示，按上面说明填 Token 即可。
pause >nul

@echo off
setlocal
cd /d "%~dp0"
set LOG=%~dp0first_push_log.txt
echo ===== 首次上传 开始于 %date% %time% ===== > "%LOG%"
echo 工作目录: %CD% >> "%LOG%"
echo.
echo [步骤] 检查 git ...
where git >nul 2>&1
if errorlevel 1 (
  echo [错误] 未找到 git，请安装 Git for Windows 并勾选 Add to PATH。>> "%LOG%"
  goto needauth
)
echo [步骤] 1/3 拉取远端 main ...
git fetch origin main >> "%LOG%" 2>&1
if errorlevel 1 (
  echo [失败] git fetch 失败，多半是还没登录 GitHub。>> "%LOG%"
  goto needauth
)
echo [步骤] 2/3 合并（以本机版本为准）...
git merge --allow-unrelated-histories -X ours origin/main >> "%LOG%" 2>&1
if errorlevel 1 (
  echo [提示] 合并未自动完成，继续尝试推送。>> "%LOG%"
) else (
  echo [ok] 合并完成。>> "%LOG%"
)
echo [步骤] 3/3 推送到 GitHub ...
git push -u origin main >> "%LOG%" 2>&1
if errorlevel 1 (
  echo [失败] git push 失败。>> "%LOG%"
  goto needauth
)
echo [ok] 推送成功。>> "%LOG%"
goto done

:needauth
echo.
echo 解决办法：推送需要 GitHub 身份。
echo   1) 打开 https://github.com/settings/tokens 生成 Token（勾选 repo 权限）
echo   2) 重新双击本文件；若弹窗要用户名/密码：
echo        用户名 = 你的 GitHub 账号
echo        密码  = 刚生成的 Token（不是登录密码）
echo 详见 first_push_log.txt

:done
echo.
echo ===== 运行结束。结果见 first_push_log.txt =====
echo 输入 exit 并回车可关闭此窗口。
cmd /k

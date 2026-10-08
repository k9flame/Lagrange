@echo off
chcp 65001 >nul
setlocal
cd /d %~dp0
echo ============================================================
echo   拉格朗日 数据采集 - MuMu 一键启动 (只读观察)
echo ============================================================
where python >nul 2>nul
if errorlevel 1 (
  echo [X] 未找到 python，请先安装 Python 3 并勾选 "Add python.exe to PATH"
  pause & exit /b 1
)

echo [1/3] 安装/检查依赖 (mitmproxy, PyYAML)...
python -m pip install -r "..\requirements.txt"
if errorlevel 1 ( echo [X] 依赖安装失败 & pause & exit /b 1 )

echo.
echo [2/3] 你的本机 IPv4 (MuMu 里代理要填这个)：
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /i "IPv4"') do echo     %%a
echo.
echo [3/3] 启动 mitmdump，监听 0.0.0.0:8080 ...
echo     保持本窗口开启；抓包写入 ..\dump ；停止按 Ctrl-C
echo.
where mitmdump >nul 2>nul
if errorlevel 1 (
  python -m mitmproxy.tools.dump -s "..\mitmproxy_addon.py" --listen-host 0.0.0.0 --listen-port 8080
) else (
  mitmdump -s "..\mitmproxy_addon.py" --listen-host 0.0.0.0 --listen-port 8080
)
pause

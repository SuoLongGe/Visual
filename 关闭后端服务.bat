@echo off
echo 正在关闭后端服务...
taskkill /F /PID 17524
if %errorlevel% == 0 (
    echo 后端服务已关闭
) else (
    echo 关闭失败，请手动关闭
)
pause


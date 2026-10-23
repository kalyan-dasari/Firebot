@echo off
setlocal
cd /d "%~dp0"

if exist "%LOCALAPPDATA%\Android\Sdk\platform-tools" (
    set "PATH=%LOCALAPPDATA%\Android\Sdk\platform-tools;%PATH%"
)
if exist "C:\platform-tools" (
    set "PATH=C:\platform-tools;%PATH%"
)

py -m pip install -r requirements.txt
py slice_bot.py %*
pause


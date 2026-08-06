@echo off
setlocal
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0script\harness-cli.ps1" %*
exit /b %ERRORLEVEL%

@echo off
setlocal

set "SCRIPT_DIR=%~dp0"
set "BOOTSTRAP=%SCRIPT_DIR%scripts\mvp_bootstrap.bat"

if not exist "%BOOTSTRAP%" (
  echo [ERR ] Script nao encontrado: "%BOOTSTRAP%"
  endlocal & exit /b 1
)

call "%BOOTSTRAP%" %*
set "EXIT_CODE=%ERRORLEVEL%"
endlocal & exit /b %EXIT_CODE%

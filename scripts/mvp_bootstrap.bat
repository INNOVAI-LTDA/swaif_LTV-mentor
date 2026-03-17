@echo off
setlocal

set "SCRIPT_DIR=%~dp0"
set "SCRIPT=%SCRIPT_DIR%mvp_bootstrap.py"

where py >nul 2>nul
if %ERRORLEVEL%==0 (
  py -3 "%SCRIPT%" %*
  set "EXIT_CODE=%ERRORLEVEL%"
  endlocal & exit /b %EXIT_CODE%
)

where python >nul 2>nul
if %ERRORLEVEL%==0 (
  python "%SCRIPT%" %*
  set "EXIT_CODE=%ERRORLEVEL%"
  endlocal & exit /b %EXIT_CODE%
)

echo [ERR ] Python nao encontrado no PATH.
endlocal & exit /b 1

@echo off
REM Dark Web OSINT Daemon - Windows Service Wrapper
REM Usage: osint-service.bat [install|remove|start|stop|status]

setlocal enabledelayedexpansion

set SERVICE_NAME=DarkWebOSINT
set DISPLAY_NAME=Dark Web OSINT Monitoring Service
set PYTHON_SCRIPT=%~dp0daemon.py
set VENV_PYTHON=%~dp0.venv\Scripts\python.exe

if "%1"=="" (
    color 0A
    cls
    echo.
    echo Dark Web OSINT Service Manager
    echo Usage: osint-service.bat [command]
    echo.
    echo Commands:
    echo   install    - Install as Windows service
    echo   remove     - Remove Windows service
    echo   start      - Start the service
    echo   stop       - Stop the service
    echo   status     - Check service status
    echo.
    pause
    goto :eof
)

if "%1"=="install" goto :install
if "%1"=="remove" goto :remove
if "%1"=="start" goto :start
if "%1"=="stop" goto :stop
if "%1"=="status" goto :status
echo Unknown command: %1
goto :eof

:install
echo Installing %DISPLAY_NAME%...
nssm install %SERVICE_NAME% "%VENV_PYTHON%" "%PYTHON_SCRIPT% --start"
nssm set %SERVICE_NAME% AppDirectory "%~dp0"
nssm set %SERVICE_NAME% AppStdout "%~dp0logs\stdout.log"
nssm set %SERVICE_NAME% AppStderr "%~dp0logs\stderr.log"
nssm set %SERVICE_NAME% AppRotateFiles 1
nssm set %SERVICE_NAME% AppRotateOnline 1
nssm set %SERVICE_NAME% AppRestartDelay 5000
echo Service installed successfully!
echo Run "osint-service.bat start" to start the service
goto :eof

:remove
echo Removing %DISPLAY_NAME%...
nssm stop %SERVICE_NAME% 0
nssm remove %SERVICE_NAME% confirm
echo Service removed successfully!
goto :eof

:start
echo Starting %DISPLAY_NAME%...
nssm start %SERVICE_NAME%
timeout /t 2 /nobreak
goto :status

:stop
echo Stopping %DISPLAY_NAME%...
nssm stop %SERVICE_NAME% 0
echo Service stopped
goto :eof

:status
echo Checking %DISPLAY_NAME% status...
nssm status %SERVICE_NAME%
if errorlevel 0 (
    echo Service status: RUNNING
) else (
    echo Service status: NOT RUNNING
)
goto :eof

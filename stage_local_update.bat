@echo off
setlocal

set "ROOT=%~dp0"
set "DISTDIR=%ROOT%dist"
set "TESTDIR=%DISTDIR%\update-test"
set "VERSION=%~1"
set "SOURCE_EXE=%~2"

if "%VERSION%"=="" (
    echo Usage: stage_local_update.bat VERSION [SOURCE_EXE]
    echo Example: stage_local_update.bat 1.0.16 "%DISTDIR%\GoPoint.exe"
    exit /b 1
)

if "%SOURCE_EXE%"=="" set "SOURCE_EXE=%DISTDIR%\GoPoint.exe"

if not exist "%SOURCE_EXE%" (
    echo Source EXE not found: %SOURCE_EXE%
    exit /b 1
)

if not exist "%TESTDIR%" mkdir "%TESTDIR%"

copy /y "%SOURCE_EXE%" "%TESTDIR%\GoPoint.exe" >nul

(
    echo {
    echo   "version": "%VERSION%",
    echo   "url": "GoPoint.exe"
    echo }
) > "%TESTDIR%\update.json"

echo Local update staged:
echo   Folder : %TESTDIR%
echo   Version: %VERSION%
echo   EXE    : %SOURCE_EXE%

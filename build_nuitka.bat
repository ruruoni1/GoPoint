@echo off
setlocal

set "ROOT=%~dp0"
set "PYTHON=%ROOT%venv\Scripts\python.exe"
set "OUTDIR=%ROOT%build\nuitka"
set "DISTDIR=%ROOT%dist"
set "VERSIONED_EXE=GoPoint_v1.0.11.exe"

if not exist "%PYTHON%" (
    echo Python executable not found: %PYTHON%
    exit /b 1
)

if exist "%OUTDIR%" rmdir /s /q "%OUTDIR%"
if not exist "%DISTDIR%" mkdir "%DISTDIR%"

"%PYTHON%" -m nuitka ^
  --onefile ^
  --zig ^
  --assume-yes-for-downloads ^
  --enable-plugins=pyqt6 ^
  --windows-console-mode=disable ^
  --include-data-files="%ROOT%icon.png=icon.png" ^
  --windows-icon-from-ico="%ROOT%icon.png" ^
  --output-dir="%OUTDIR%" ^
  --output-filename=GoPoint.exe ^
  --product-name=GoPoint ^
  --company-name=GoVerseTV ^
  --file-version=1.0.11.0 ^
  --product-version=1.0.11 ^
  --file-description="GoPoint mouse trail overlay" ^
  "%ROOT%GoPoint.py"

if errorlevel 1 exit /b %errorlevel%

copy /y "%OUTDIR%\GoPoint.exe" "%DISTDIR%\GoPoint.exe" >nul
copy /y "%OUTDIR%\GoPoint.exe" "%DISTDIR%\%VERSIONED_EXE%" >nul

echo Built:
echo   %DISTDIR%\GoPoint.exe
echo   %DISTDIR%\%VERSIONED_EXE%

@echo off
REM Build the SM809 Pro app into a single portable .exe (no console window).
REM Output: dist\control-centre-v5\SM809Pro.exe
REM Requires: pip install pyinstaller  (plus PySide6 + hidapi, already used by the app)
echo Building SM809Pro.exe with an isolated DLL search path ...
python tools\build_test.py
if errorlevel 1 exit /b 1
echo.
echo Done. See dist\control-centre-v5\SM809Pro.exe
pause

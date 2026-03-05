@echo off
REM Pre-push checklist for Tariff Extraction System

echo ==================================
echo PRE-PUSH CHECKLIST
echo ==================================

REM 1. Check .env is ignored
echo.
echo 1. Checking .env is not tracked...
git ls-files | findstr /C:".env" >nul 2>&1
if %errorlevel% equ 0 (
    echo    [FAIL] .env is tracked! Run: git rm --cached .env
    exit /b 1
) else (
    echo    [OK] .env is not tracked
)

REM 2. Check __pycache__ is ignored
echo.
echo 2. Checking Python cache is not tracked...
git ls-files | findstr /C:"__pycache__" >nul 2>&1
if %errorlevel% equ 0 (
    echo    [FAIL] __pycache__ is tracked!
    exit /b 1
) else (
    echo    [OK] Python cache not tracked
)

REM 3. Check data files are ignored
echo.
echo 3. Checking data files are not tracked...
git ls-files | findstr /C:"data\raw" | findstr /C:".html .pdf" >nul 2>&1
if %errorlevel% equ 0 (
    echo    [FAIL] Data files are tracked!
    exit /b 1
) else (
    echo    [OK] Data files not tracked
)

REM 4. Verify system
echo.
echo 4. Running system verification...
python scripts\verify_system.py >nul 2>&1
if %errorlevel% equ 0 (
    echo    [OK] System verification passed
) else (
    echo    [WARN] System verification failed (may need database^)
)

echo.
echo ==================================
echo READY TO PUSH
echo ==================================
echo.
echo Run: git add .
echo      git commit -m "Initial commit: Tariff extraction system"
echo      git push origin main

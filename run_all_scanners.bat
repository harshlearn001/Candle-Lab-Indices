@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

REM ======================================
REM FORCE AUTO MODE DEFAULT
REM ======================================
if "%AUTO_MODE%"=="" set AUTO_MODE=1

echo AUTO_MODE = %AUTO_MODE%

REM ======================================
REM PYTHON PATH
REM ======================================
set "PYTHON=C:\Users\Harshal\anaconda3\python.exe"

REM ======================================
REM PROJECT ROOT
REM ======================================
set "ROOT=H:\Candle-Lab-Indices"

REM ======================================
REM PAUSE CONTROL
REM ======================================
if /I "%AUTO_MODE%"=="1" (
    set "PAUSE_CMD="
) else (
    set "PAUSE_CMD=pause"
)

REM ======================================
REM HEADER
REM ======================================
cls

echo ======================================
echo   CANDLE-LAB INDEX PIPELINE STARTED
echo ======================================
echo.

set "start=%time%"

REM ======================================
REM RUN ALL SCANNERS
REM ======================================

call :run "%ROOT%\Scanners\pcr_day" "01_pcr_engine.py"

call :run "%ROOT%\Scanners\adx" "01_adx_index.py"

call :run "%ROOT%\Scanners\engulfing_candle" "01_bullish_engulfing_exact.py"
call :run "%ROOT%\Scanners\engulfing_candle" "02_bearish_engulfing_exact.py"

call :run "%ROOT%\Scanners\gravestone_candle" "01_gravestone_doji_in_uptrend.py"

call :run "%ROOT%\Scanners\Hammer" "hammer_confirmation.py"

call :run "%ROOT%\Scanners\shooting_star" "01_shooting_star_uptrend.py"

call :run "%ROOT%\Scanners\hangingman" "01_hanging_man_scan.py"

call :run "%ROOT%\Scanners\harami" "01_harami_scan.py"

call :run "%ROOT%\Scanners\inside_bar_scan" "inside_bar_scan.py"

call :run "%ROOT%\Scanners\nr7" "fno_nr7_scan.py"

call :run "%ROOT%\Scanners\rsi" "01_rsi_scan.py"

call :run "%ROOT%\Scanners\rsi_divergence" "02_rsi_divergence_scan.py"

call :run "%ROOT%\Scanners\morning_evening_star" "01_morning_star_scanner.py"
call :run "%ROOT%\Scanners\morning_evening_star" "02_evening_star_scanner.py"

call :run "%ROOT%\Scanners\breadth" "01_index_breadth_engine.py"

call :run "%ROOT%\Scanners\vwap" "01_vwap_index.py"

REM ======================================
REM PIPELINE COMPLETED
REM ======================================

echo.
echo ======================================
echo   ALL INDEX SCANNERS COMPLETED
echo ======================================

set "end=%time%"

echo Started at: %start%
echo Ended at  : %end%

echo.

%PAUSE_CMD%

exit /b 0

REM ======================================
REM ERROR HANDLER
REM ======================================
:error

echo.
echo ======================================
echo ❌ PIPELINE FAILED
echo ======================================
echo Failed at step above
echo.

%PAUSE_CMD%

exit /b 1

REM ======================================
REM FUNCTION
REM ======================================
:run

set "SCRIPT_DIR=%~1"
set "SCRIPT_NAME=%~2"

echo --------------------------------------
echo Running: %SCRIPT_NAME%
echo --------------------------------------

cd /d "%SCRIPT_DIR%"

set "step_start=%time%"

"%PYTHON%" "%SCRIPT_NAME%"

set "step_end=%time%"

if not "%ERRORLEVEL%"=="0" (
    echo.
    echo ❌ ERROR in %SCRIPT_NAME%
    goto :error
)

echo ✅ SUCCESS: %SCRIPT_NAME%
echo Time: %step_start% → %step_end%
echo.

goto :eof
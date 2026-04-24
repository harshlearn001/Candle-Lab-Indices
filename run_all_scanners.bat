@echo off
setlocal enabledelayedexpansion

echo ======================================
echo   CANDLE-LAB INDEX PIPELINE STARTED
echo ======================================

set start=%time%

REM ======================================
REM OPTIONAL: Activate Conda (safe method)
REM ======================================
CALL "C:\Users\Harshal\anaconda3\condabin\conda.bat" activate base

REM ======================================
REM FUNCTION CALLS
REM ======================================

REM PCR
cd /d H:\Candle-Lab-Indices\Scanners\pcr_day
call :run_script 01_pcr_engine.py

REM ADX
cd /d H:\Candle-Lab-Indices\Scanners\adx
call :run_script 01_adx_index.py

REM ENGULFING
cd /d H:\Candle-Lab-Indices\Scanners\engulfing_candle
call :run_script 01_bullish_engulfing_exact.py
call :run_script 02_bearish_engulfing_exact.py

REM CANDLE PATTERNS
cd /d H:\Candle-Lab-Indices\Scanners\gravestone_candle
call :run_script 01_gravestone_doji_in_uptrend.py

cd /d H:\Candle-Lab-Indices\Scanners\Hammer
call :run_script hammer_confirmation.py

cd /d H:\Candle-Lab-Indices\Scanners\shooting_star
call :run_script 01_shooting_star_uptrend.py

cd /d H:\Candle-Lab-Indices\Scanners\hangingman
call :run_script 01_hanging_man_scan.py

cd /d H:\Candle-Lab-Indices\Scanners\harami
call :run_script 01_harami_scan.py

cd /d H:\Candle-Lab-Indices\Scanners\inside_bar_scan
call :run_script inside_bar_scan.py

cd /d H:\Candle-Lab-Indices\Scanners\nr7
call :run_script fno_nr7_scan.py

REM MOMENTUM
cd /d H:\Candle-Lab-Indices\Scanners\rsi
call :run_script 01_rsi_scan.py

cd /d H:\Candle-Lab-Indices\Scanners\rsi_divergence
call :run_script 02_rsi_divergence_scan.py

REM MORNING / EVENING
cd /d H:\Candle-Lab-Indices\Scanners\morning_evening_star
call :run_script 01_morning_star_scanner.py
call :run_script 02_evening_star_scanner.py

REM BREADTH (FIXED)
cd /d H:\Candle-Lab-Indices\Scanners\breadth
call :run_script 01_index_breadth_engine.py

REM VWAP (ADDED)
cd /d H:\Candle-Lab-Indices\Scanners\vwap
call :run_script 01_vwap_index.py

REM ======================================
REM END
REM ======================================
echo.
echo ======================================
echo   ALL INDEX SCANNERS COMPLETED
echo ======================================

set end=%time%
echo Started at: %start%
echo Ended at  : %end%

pause
exit /b


REM ======================================
REM FUNCTION
REM ======================================
:run_script
echo --------------------------------------
echo Running: %~1
echo --------------------------------------

REM Use direct python path (FIX)
"C:\Users\Harshal\anaconda3\python.exe" "%~1"

IF %ERRORLEVEL% NEQ 0 (
    echo ERROR in %~1
) ELSE (
    echo SUCCESS: %~1
)

exit /b
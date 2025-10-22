@echo off
chcp 65001 > nul
cls

echo.
echo ================================================
echo          MARCO PHARMA - DEMARRAGE
echo ================================================
echo.

REM Verification Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERREUR] Python non installe
    pause
    exit /b 1
)

echo [1/3] Python OK

REM Installation rapide
echo [2/3] Installation dependances...
pip install -q Flask Flask-SQLAlchemy Flask-Login PyMySQL >nul 2>&1

REM Lancement
echo [3/3] Demarrage application...
echo.
echo URL: http://localhost:5000
echo Login: admin / admin123
echo.
echo Appuyez sur Ctrl+C pour arreter
echo ================================================
echo.

REM Ouvrir navigateur
start http://localhost:5000

REM Lancer app
python run.py

if errorlevel 1 (
    echo.
    echo [ERREUR] Verifiez que MySQL est demarre
    echo.
)

pause


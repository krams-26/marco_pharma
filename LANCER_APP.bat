@echo off
chcp 65001 > nul
cls

echo.
echo =====================================================
echo          MARCO PHARMA - LANCEMENT RAPIDE
echo =====================================================
echo.

REM Verification Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [X] Python n'est pas installe
    echo.
    echo Telechargez Python sur: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo [OK] Python detecte

REM Verification MySQL (optionnel - ne bloque pas)
echo.
echo [INFO] Verification de MySQL...
python -c "import pymysql; pymysql.connect(host='localhost', user='root', password='', database='marphar').close(); print('[OK] MySQL connecte')" 2>nul
if errorlevel 1 (
    echo [ATTENTION] MySQL non accessible - Verifiez que:
    echo   1. WAMP/XAMPP est demarre
    echo   2. La base 'marphar' existe
    echo   3. Le mot de passe root est vide
    echo.
    echo Voulez-vous continuer quand meme? (O/N)
    choice /C ON /N /M ">"
    if errorlevel 2 exit /b 1
)

REM Installation dependances
echo.
echo [INFO] Installation des dependances...
pip install --quiet Flask Flask-SQLAlchemy Flask-Login PyMySQL Werkzeug openpyxl 2>nul
if errorlevel 1 (
    echo [!] Erreur installation - Continuons quand meme
)
echo [OK] Dependances installees

REM Lancer l'application
echo.
echo =====================================================
echo   APPLICATION EN COURS DE DEMARRAGE...
echo =====================================================
echo.
echo URL: http://localhost:5000
echo.
echo COMPTES PAR DEFAUT:
echo   - admin / admin123
echo   - caissier / caissier123
echo   - vendeur / vendeur123
echo.
echo [INFO] Appuyez sur Ctrl+C pour arreter
echo =====================================================
echo.

REM Ouvrir navigateur apres 4 secondes
start /B cmd /c "timeout /t 4 /nobreak >nul 2>&1 && start http://localhost:5000" >nul 2>&1

REM Lancer Flask
echo [INFO] Demarrage Flask...
python run.py
echo.

REM Gestion erreur
if errorlevel 1 (
    echo.
    echo =====================================================
    echo [ERREUR] L'application s'est arretee
    echo =====================================================
    echo.
    echo Solutions:
    echo   1. Verifiez que MySQL est demarre (WAMP/XAMPP)
    echo   2. Assurez-vous que la base 'marphar' existe
    echo   3. Lancez: python diagnostic_approfondi.py
    echo.
)

pause


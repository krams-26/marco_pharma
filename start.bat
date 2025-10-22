@echo off
title Marco Pharma - Systeme de Gestion de Pharmacie
color 0A

echo.
echo ========================================
echo   MARCO PHARMA - SYSTEME DE GESTION
echo ========================================
echo.

REM Verifier si Python est installe
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERREUR] Python n'est pas installe ou pas dans le PATH
    echo Veuillez installer Python 3.8+ depuis https://python.org
    pause
    exit /b 1
)

echo [OK] Python detecte
echo.

REM Verifier si les dependances sont installees
echo [INFO] Verification des dependances...
pip show flask >nul 2>&1
if errorlevel 1 (
    echo [INFO] Installation des dependances...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo [ERREUR] Echec de l'installation des dependances
        pause
        exit /b 1
    )
    echo [OK] Dependances installees
) else (
    echo [OK] Dependances deja installees
)

echo.
echo [INFO] Demarrage de l'application...
echo [INFO] L'application sera accessible sur: http://localhost:5000
echo [INFO] Appuyez sur Ctrl+C pour arreter
echo.

REM Demarrer l'application
python run.py

pause

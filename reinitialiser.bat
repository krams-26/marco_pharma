@echo off
chcp 65001 >nul
cls
echo ╔══════════════════════════════════════════════════════════╗
echo ║                                                          ║
echo ║     REINITIALISATION DE LA BASE DE DONNEES              ║
echo ║                                                          ║
echo ╚══════════════════════════════════════════════════════════╝
echo.
echo.
echo ⚠  ATTENTION: Cette operation va:
echo    - Supprimer toutes les donnees actuelles
echo    - Recreer la base de donnees
echo    - Rajouter les donnees de test
echo.
echo.
pause
echo.
echo.

echo [1/3] Arret de l'application...
taskkill /F /IM python.exe >nul 2>&1
echo [OK] Application arretee
echo.

echo [2/3] Reinitialisation de la base de donnees...
python reset_db.py
if %ERRORLEVEL% EQU 0 (
    echo [OK] Base de donnees reinitialisee
) else (
    echo [ERREUR] Echec de la reinitialisation
    pause
    exit /b 1
)
echo.

echo [3/3] Ajout des donnees de test...
python seed_data.py
if %ERRORLEVEL% EQU 0 (
    echo [OK] Donnees de test ajoutees
) else (
    echo [ERREUR] Echec de l'ajout des donnees
    pause
    exit /b 1
)
echo.

echo ══════════════════════════════════════════════════════════
echo.
echo ✅ REINITIALISATION TERMINEE AVEC SUCCES!
echo.
echo Pour demarrer l'application:
echo    - Double-cliquez sur: start.bat
echo    - OU executez: python run.py
echo.
echo Identifiants admin:
echo    Username: admin
echo    Password: admin123
echo.
echo ══════════════════════════════════════════════════════════
echo.
pause


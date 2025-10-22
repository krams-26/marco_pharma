@echo off
chcp 65001 >nul
cls
echo ╔══════════════════════════════════════════════════════════╗
echo ║                                                          ║
echo ║     CONFIGURATION MYSQL POUR MARCO-PHARMA               ║
echo ║                                                          ║
echo ╚══════════════════════════════════════════════════════════╝
echo.
echo.

echo [1/4] Vérification de WAMP/MySQL...
echo.

REM Chercher le service MySQL de WAMP
net start | findstr /i "mysql" >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo [OK] MySQL est en cours d'exécution
) else (
    echo [INFO] MySQL n'est pas démarré comme service
    echo.
    echo Tentative de démarrage de MySQL via WAMP...
    
    if exist "C:\wamp64\wampmanager.exe" (
        echo [INFO] WAMP trouvé. Démarrage en cours...
        start "" "C:\wamp64\wampmanager.exe"
        timeout /t 5 /nobreak >nul
        echo.
        echo ⚠  IMPORTANT: Assurez-vous que WAMP est démarré (icône verte)
        echo    et que MySQL est actif avant de continuer.
        echo.
        pause
    ) else (
        echo [ATTENTION] WAMP n'est pas trouvé au chemin standard
        echo.
        echo Veuillez:
        echo   1. Démarrer WAMP manuellement
        echo   2. Vérifier que l'icône WAMP est verte
        echo   3. Vérifier que MySQL est actif
        echo.
        pause
    )
)

echo.
echo [2/4] Configuration de la base de données MySQL...
echo.

python setup_mysql.py
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERREUR] Échec de la configuration MySQL
    echo.
    echo Veuillez vérifier que:
    echo   - WAMP est démarré (icône verte)
    echo   - MySQL est actif dans WAMP
    echo   - Le port 3306 est disponible
    echo.
    pause
    exit /b 1
)

echo.
echo [3/4] Arrêt de l'application en cours...
taskkill /F /IM python.exe >nul 2>&1
echo [OK] Application arrêtée
echo.

echo [4/4] Initialisation de la base de données...
echo.
python reset_db.py
if %ERRORLEVEL% EQU 0 (
    echo [OK] Base de données initialisée
) else (
    echo [ERREUR] Échec de l'initialisation
    pause
    exit /b 1
)

echo.
echo Ajout des données de test...
python seed_data.py
if %ERRORLEVEL% EQU 0 (
    echo [OK] Données de test ajoutées
) else (
    echo [ERREUR] Échec de l'ajout des données
    pause
    exit /b 1
)

echo.
echo ══════════════════════════════════════════════════════════
echo.
echo ✅ CONFIGURATION MYSQL TERMINÉE AVEC SUCCÈS!
echo.
echo Base de données: marphar (MySQL)
echo.
echo Pour démarrer l'application:
echo    - Double-cliquez sur: start.bat
echo    - OU exécutez: python run.py
echo.
echo Identifiants admin:
echo    Username: admin
echo    Password: admin123
echo.
echo ══════════════════════════════════════════════════════════
echo.
pause


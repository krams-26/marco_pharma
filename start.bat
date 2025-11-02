@echo off
title MARCO PHARMA - Systeme de Gestion Pharmaceutique
color 0A

echo.
echo ========================================
echo    MARCO PHARMA - DEMARRAGE
echo ========================================
echo.

echo [1/3] Verification de Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python n'est pas installe ou pas dans le PATH
    echo 💡 Installez Python depuis https://python.org
    pause
    exit /b 1
)
echo ✅ Python detecte

echo.
echo [2/3] Installation des dependances...
pip install -r requirements.txt >nul 2>&1
if errorlevel 1 (
    echo ⚠️  Certaines dependances peuvent manquer
    echo 💡 Essayez: pip install -r requirements.txt
)

echo.
echo [3/3] Demarrage de l'application...
echo.
echo 🌐 URL: http://localhost:200
echo 🌐 Reseau: http://192.168.1.154:200
echo 👤 Admin: admin / admin123
echo.
echo ========================================
echo.

python run.py

if errorlevel 1 (
    echo.
    echo ❌ Erreur de demarrage
    echo 💡 Verifiez que tous les modules sont installes
    echo 💡 Essayez: pip install -r requirements.txt
    echo.
    pause
)
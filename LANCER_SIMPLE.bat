@echo off
REM Script de lancement ultra-simplifie
cls
echo Demarrage de Marco-Pharma...
echo.

REM Installer dependances si necessaire
pip install -q Flask Flask-SQLAlchemy Flask-Login PyMySQL 2>nul

REM Lancer
start http://localhost:5000
python run.py

pause


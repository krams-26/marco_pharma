#!/usr/bin/env python3
"""
Script de lancement pour Marco Pharma
Version multi-plateforme (Windows, Linux, macOS)
"""

import os
import sys
import subprocess
import platform

def check_python_version():
    """Vérifier la version de Python"""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8+ requis")
        print(f"   Version actuelle: {sys.version}")
        return False
    print(f"✅ Python {sys.version.split()[0]} détecté")
    return True

def check_dependencies():
    """Vérifier et installer les dépendances"""
    try:
        import flask
        print("✅ Flask déjà installé")
        return True
    except ImportError:
        print("📦 Installation des dépendances...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
            print("✅ Dépendances installées")
            return True
        except subprocess.CalledProcessError:
            print("❌ Erreur lors de l'installation des dépendances")
            return False

def check_database():
    """Vérifier la configuration de la base de données"""
    try:
        from app import create_app
        from app.models import db
        
        app = create_app()
        with app.app_context():
            # Tenter une connexion simple
            db.engine.execute('SELECT 1')
            print("✅ Base de données accessible")
            return True
    except Exception as e:
        print(f"⚠️  Problème de base de données: {e}")
        print("   Assurez-vous que MySQL est démarré et que la base 'marphar' existe")
        return False

def start_application():
    """Démarrer l'application"""
    print("\n🚀 Démarrage de Marco Pharma...")
    print("   URL: http://localhost:5000")
    print("   Appuyez sur Ctrl+C pour arrêter")
    print("-" * 50)
    
    try:
        from run import app
        app.run(host='0.0.0.0', port=5000, debug=True)
    except KeyboardInterrupt:
        print("\n👋 Arrêt de l'application")
    except Exception as e:
        print(f"\n❌ Erreur: {e}")

def main():
    """Fonction principale"""
    print("=" * 60)
    print("🏥 MARCO PHARMA - SYSTÈME DE GESTION DE PHARMACIE")
    print("=" * 60)
    print()
    
    # Vérifications
    if not check_python_version():
        sys.exit(1)
    
    if not check_dependencies():
        sys.exit(1)
    
    if not check_database():
        print("⚠️  Continuons malgré le problème de base de données...")
    
    # Démarrage
    start_application()

if __name__ == "__main__":
    main()
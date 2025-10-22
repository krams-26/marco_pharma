"""
Script de lancement Python multi-plateforme pour Marco-Pharma
Compatible Windows, Linux, macOS
"""
import subprocess
import sys
import os
import time
import webbrowser

def print_banner():
    """Afficher la bannière de démarrage"""
    print("=" * 60)
    print(" " * 15 + "MARCO PHARMA")
    print(" " * 10 + "Systeme de Gestion de Pharmacie")
    print("=" * 60)
    print()

def check_python():
    """Vérifier la version de Python"""
    print("[1/5] Verification de Python...")
    version = sys.version_info
    if version.major >= 3 and version.minor >= 8:
        print(f"  [OK] Python {version.major}.{version.minor}.{version.micro}")
        return True
    else:
        print(f"  [ERREUR] Python 3.8+ requis (actuel: {version.major}.{version.minor})")
        return False

def check_mysql():
    """Vérifier la connexion MySQL"""
    print("\n[2/5] Verification de MySQL...")
    try:
        import pymysql
        conn = pymysql.connect(
            host='localhost',
            user='root',
            password='',
            database='marphar'
        )
        conn.close()
        print("  [OK] MySQL connecte - Base 'marphar' accessible")
        return True
    except ImportError:
        print("  [AVERTISSEMENT] Module PyMySQL non installe")
        return False
    except Exception as e:
        print(f"  [AVERTISSEMENT] MySQL non accessible: {str(e)}")
        print("  [INFO] Verifiez que WAMP/XAMPP est demarre")
        return False

def install_dependencies():
    """Installer les dépendances"""
    print("\n[3/5] Installation des dependances...")
    try:
        subprocess.check_call([
            sys.executable, '-m', 'pip', 'install', '--quiet', 
            '--upgrade', 'pip'
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        subprocess.check_call([
            sys.executable, '-m', 'pip', 'install', '--quiet',
            '-r', 'requirements.txt'
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        print("  [OK] Dependances installees")
        return True
    except Exception as e:
        print(f"  [AVERTISSEMENT] Certaines dependances manquantes: {str(e)}")
        print("  [INFO] L'application tentera de demarrer quand meme...")
        return True

def open_browser():
    """Ouvrir le navigateur après un délai"""
    time.sleep(4)
    webbrowser.open('http://localhost:5000')

def launch_app():
    """Lancer l'application Flask"""
    print("\n[4/5] Lancement de l'application...")
    print("\n" + "=" * 60)
    print("  APPLICATION DEMARREE")
    print("=" * 60)
    print("\n  URL: http://localhost:5000")
    print("\n  COMPTES PAR DEFAUT:")
    print("    - admin / admin123")
    print("    - caissier / caissier123")
    print("    - vendeur / vendeur123")
    print("\n  Appuyez sur Ctrl+C pour arreter")
    print("=" * 60)
    print()
    
    # Ouvrir navigateur en arrière-plan
    import threading
    browser_thread = threading.Thread(target=open_browser, daemon=True)
    browser_thread.start()
    
    # Lancer Flask
    try:
        from app import create_app
        app = create_app()
        app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)
    except KeyboardInterrupt:
        print("\n\n[INFO] Application arretee par l'utilisateur")
    except Exception as e:
        print(f"\n\n[ERREUR] L'application s'est arretee: {str(e)}")
        print("\n[SOLUTIONS]:")
        print("  1. Verifiez que MySQL est demarre")
        print("  2. Verifiez que la base 'marphar' existe")
        print("  3. Lancez: python diagnostic_approfondi.py")
        return False
    
    return True

def main():
    """Point d'entrée principal"""
    print_banner()
    
    # Vérifications
    if not check_python():
        input("\nAppuyez sur Entree pour quitter...")
        return 1
    
    check_mysql()  # Non bloquant
    
    if not install_dependencies():
        response = input("\nContinuer quand meme? (O/N): ")
        if response.upper() != 'O':
            return 1
    
    # Lancement
    success = launch_app()
    
    print("\n[5/5] Fermeture...")
    return 0 if success else 1

if __name__ == '__main__':
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n[INFO] Arret demande par l'utilisateur")
        sys.exit(0)


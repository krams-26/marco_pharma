"""
Script de lancement pour tester le Journal d'Activites
"""

import subprocess
import sys
import os

def run_python_script(script_file):
    """Execute un script Python"""
    try:
        print(f"Execution de {script_file}...")
        
        result = subprocess.run([sys.executable, script_file], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"SUCCESS: {script_file} execute avec succes")
            print(result.stdout)
            return True
        else:
            print(f"ERREUR lors de l'execution de {script_file}:")
            print(result.stderr)
            return False
            
    except Exception as e:
        print(f"ERREUR lors de l'execution de {script_file}: {e}")
        return False

def main():
    """Fonction principale"""
    print("CONFIGURATION DU JOURNAL D'ACTIVITES")
    print("=" * 50)
    
    # Verifier que nous sommes dans le bon repertoire
    if not os.path.exists('app'):
        print("ERREUR: Repertoire 'app' non trouve. Executez depuis la racine du projet.")
        return
    
    # 1. Generation des donnees de test
    print("\nETAPE 1: Generation des donnees de test...")
    
    if not run_python_script('test_audit_data.py'):
        print("ECHEC de la generation des donnees de test")
        return
    
    # 2. Instructions de test
    print("\nINSTRUCTIONS DE TEST:")
    print("=" * 50)
    print("1. Lancez l'application:")
    print("   python main.py")
    print()
    print("2. Connectez-vous avec admin/admin123")
    print()
    print("3. Testez ces pages:")
    print("   - http://localhost:5000/audits/ - Liste des activites")
    print("   - http://localhost:5000/audits/dashboard - Dashboard avec graphiques")
    print("   - http://localhost:5000/audits/alerts - Activites suspectes")
    print()
    print("4. Testez les filtres par module, type, resultat, date")
    print("5. Testez les exports Excel/CSV")
    print("6. Tentez une connexion incorrecte pour voir les alertes")
    print()
    print("VOTRE JOURNAL D'ACTIVITES EST PRET!")
    print("=" * 50)

if __name__ == '__main__':
    main()

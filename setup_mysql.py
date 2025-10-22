import pymysql
import sys
import os

def setup_mysql():
    print("=" * 60)
    print("Configuration MySQL pour Marco-Pharma")
    print("=" * 60)
    print()
    
    # Paramètres MySQL par défaut pour WAMP
    host = 'localhost'
    port = 3306
    user = 'root'
    password = ''  # WAMP utilise généralement un mot de passe vide pour root
    database = 'marphar'
    
    print(f"Tentative de connexion à MySQL...")
    print(f"  Hôte: {host}")
    print(f"  Port: {port}")
    print(f"  Utilisateur: {user}")
    print()
    
    try:
        # Connexion à MySQL (sans sélectionner de base de données)
        connection = pymysql.connect(
            host=host,
            port=port,
            user=user,
            password=password
        )
        
        print("[OK] Connexion à MySQL réussie!")
        print()
        
        cursor = connection.cursor()
        
        # Vérifier si la base de données existe
        cursor.execute(f"SHOW DATABASES LIKE '{database}'")
        result = cursor.fetchone()
        
        if result:
            print(f"[INFO] La base de données '{database}' existe déjà.")
            response = input("Voulez-vous la supprimer et la recréer? (o/N): ").strip().lower()
            if response == 'o':
                cursor.execute(f"DROP DATABASE {database}")
                print(f"[OK] Base de données '{database}' supprimée.")
                cursor.execute(f"CREATE DATABASE {database} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
                print(f"[OK] Base de données '{database}' recréée.")
            else:
                print(f"[INFO] Utilisation de la base de données existante.")
        else:
            cursor.execute(f"CREATE DATABASE {database} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
            print(f"[OK] Base de données '{database}' créée avec succès!")
        
        cursor.close()
        connection.close()
        
        # Mettre à jour la configuration
        config_content = f"""import os
from datetime import timedelta

basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'mysql+pymysql://{user}:{password}@{host}:{port}/{database}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    PERMANENT_SESSION_LIFETIME = timedelta(hours=12)
    
    UPLOAD_FOLDER = 'uploads'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024
    
    ITEMS_PER_PAGE = 20
    
    CURRENCY_SYMBOL = '$'
    CURRENCY_CODE = 'USD'
    
    COMPANY_NAME = 'Pharmacie Moderne'
    COMPANY_ADDRESS = ''
    COMPANY_PHONE = ''
    COMPANY_EMAIL = ''
"""
        
        with open('app/config.py', 'w', encoding='utf-8') as f:
            f.write(config_content)
        
        print()
        print("[OK] Fichier de configuration mis à jour!")
        print()
        print("=" * 60)
        print("Configuration MySQL terminée avec succès!")
        print("=" * 60)
        print()
        print("Prochaines étapes:")
        print("  1. Arrêtez l'application si elle est en cours d'exécution (Ctrl+C)")
        print("  2. Exécutez: python reset_db.py")
        print("  3. Exécutez: python seed_data.py")
        print("  4. Exécutez: python run.py")
        print()
        print("Ou utilisez simplement: reinitialiser.bat")
        print()
        
        return True
        
    except pymysql.Error as e:
        print(f"[ERREUR] Impossible de se connecter à MySQL: {e}")
        print()
        print("Vérifications à faire:")
        print("  1. MySQL est-il démarré? Lancez WAMP et vérifiez que MySQL est actif")
        print("  2. Le port 3306 est-il disponible?")
        print("  3. Les identifiants sont-ils corrects?")
        print()
        print("Si vous utilisez WAMP, assurez-vous que:")
        print("  - WAMP est démarré (icône verte)")
        print("  - Le service MySQL est actif")
        print()
        return False
    
    except Exception as e:
        print(f"[ERREUR] Erreur inattendue: {e}")
        return False

if __name__ == '__main__':
    success = setup_mysql()
    sys.exit(0 if success else 1)


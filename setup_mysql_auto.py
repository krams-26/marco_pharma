import pymysql
import sys

def setup_mysql():
    print("=" * 60)
    print("Configuration MySQL pour Marco-Pharma")
    print("=" * 60)
    print()
    
    host = 'localhost'
    port = 3306
    user = 'root'
    password = ''
    database = 'marphar'
    
    print(f"Connexion à MySQL...")
    print(f"  Hôte: {host}:{port}")
    print(f"  Base de données: {database}")
    print()
    
    try:
        connection = pymysql.connect(
            host=host,
            port=port,
            user=user,
            password=password
        )
        
        print("[OK] Connexion réussie!")
        
        cursor = connection.cursor()
        
        cursor.execute(f"DROP DATABASE IF EXISTS {database}")
        print(f"[OK] Ancienne base supprimée (si elle existait)")
        
        cursor.execute(f"CREATE DATABASE {database} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
        print(f"[OK] Base de données '{database}' créée!")
        
        cursor.close()
        connection.close()
        
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
        
        print("[OK] Configuration mise à jour!")
        print()
        print("=" * 60)
        print("Configuration MySQL terminée!")
        print("=" * 60)
        
        return True
        
    except pymysql.Error as e:
        print(f"[ERREUR] MySQL: {e}")
        print()
        print("Assurez-vous que WAMP est démarré et MySQL est actif")
        return False

if __name__ == '__main__':
    success = setup_mysql()
    sys.exit(0 if success else 1)


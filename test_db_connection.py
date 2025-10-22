#!/usr/bin/env python3
"""
Script pour tester la connexion à la base de données MySQL sur PythonAnywhere
Utilisez ce script pour vérifier que votre configuration est correcte
"""

import os
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

print("=" * 70)
print("TEST DE CONNEXION À LA BASE DE DONNÉES")
print("=" * 70)
print()

# Vérifier les variables d'environnement
database_url = os.environ.get('DATABASE_URL')
secret_key = os.environ.get('SECRET_KEY')

print("1. Vérification des variables d'environnement...")
print(f"   DATABASE_URL: {'✅ Définie' if database_url else '❌ Non définie'}")
print(f"   SECRET_KEY: {'✅ Définie' if secret_key else '❌ Non définie'}")
print()

if not database_url:
    print("❌ ERREUR : DATABASE_URL n'est pas définie dans le fichier .env")
    print("   Créez un fichier .env avec :")
    print("   DATABASE_URL=mysql+pymysql://user:pass@host/database")
    exit(1)

if not secret_key:
    print("⚠️  AVERTISSEMENT : SECRET_KEY n'est pas définie")
    print()

# Tester la connexion
print("2. Test de connexion à la base de données...")
try:
    from app import create_app
    from app.models import db
    
    app = create_app()
    
    with app.app_context():
        # Tenter une simple requête
        db.engine.execute('SELECT 1')
        print("   ✅ Connexion réussie!")
        print()
        
        # Vérifier les tables
        print("3. Vérification des tables...")
        inspector = db.inspect(db.engine)
        tables = inspector.get_table_names()
        
        if tables:
            print(f"   ✅ {len(tables)} table(s) trouvée(s):")
            for table in sorted(tables)[:10]:  # Afficher les 10 premières
                print(f"      - {table}")
            if len(tables) > 10:
                print(f"      ... et {len(tables) - 10} autre(s)")
        else:
            print("   ⚠️  Aucune table trouvée. Exécutez db.create_all()")
        print()
        
        print("=" * 70)
        print("✅ TOUT EST PRÊT ! Votre base de données est correctement configurée.")
        print("=" * 70)
        
except Exception as e:
    print(f"   ❌ Erreur de connexion : {str(e)}")
    print()
    print("=" * 70)
    print("SUGGESTIONS DE DÉPANNAGE :")
    print("=" * 70)
    print("1. Vérifiez que DATABASE_URL est correcte dans .env")
    print("2. Vérifiez que la base de données existe sur PythonAnywhere")
    print("3. Vérifiez vos identifiants MySQL")
    print("4. Vérifiez que PyMySQL est installé : pip install PyMySQL")
    print("=" * 70)
    exit(1)


import pymysql
import sys
from app.config import Config

def create_database():
    db_url = Config.SQLALCHEMY_DATABASE_URI
    
    if 'mysql' in db_url:
        parts = db_url.split('/')
        db_name = parts[-1]
        
        base_url = '/'.join(parts[:-1])
        
        connection_parts = base_url.replace('mysql+pymysql://', '').split('@')
        
        if ':' in connection_parts[0]:
            user, password = connection_parts[0].split(':')
        else:
            user = connection_parts[0]
            password = ''
        
        host = connection_parts[1].split('/')[0] if '/' in connection_parts[1] else connection_parts[1]
        
        if ':' in host:
            host, port = host.split(':')
            port = int(port)
        else:
            port = 3306
        
        try:
            connection = pymysql.connect(
                host=host,
                user=user,
                password=password,
                port=port
            )
            
            cursor = connection.cursor()
            
            cursor.execute(f"SHOW DATABASES LIKE '{db_name}'")
            result = cursor.fetchone()
            
            if not result:
                cursor.execute(f"CREATE DATABASE {db_name} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
                print(f"✓ Base de données '{db_name}' créée avec succès!")
            else:
                print(f"✓ Base de données '{db_name}' existe déjà.")
            
            cursor.close()
            connection.close()
            
            return True
            
        except pymysql.Error as e:
            print(f"✗ Erreur MySQL: {e}")
            print("\nVérifiez que:")
            print("  1. MySQL est installé et en cours d'exécution")
            print("  2. Les informations de connexion dans app/config.py sont correctes")
            print(f"     Connexion actuelle: {user}@{host}:{port}")
            return False
    else:
        print("✓ Configuration SQLite détectée, aucune initialisation nécessaire.")
        return True

if __name__ == '__main__':
    print("Initialisation de la base de données...")
    print("=" * 50)
    
    if create_database():
        print("\n✓ Initialisation terminée avec succès!")
        print("\nVous pouvez maintenant lancer l'application avec: python run.py")
        sys.exit(0)
    else:
        print("\n✗ Échec de l'initialisation.")
        sys.exit(1)


"""
Migration MySQL: Ajouter pharmacy_id et notes a la table expenses
"""

from app import create_app
from app.models import db

def migrate():
    app = create_app()
    
    with app.app_context():
        try:
            # Verifier si les colonnes existent deja
            from sqlalchemy import inspect, text
            inspector = inspect(db.engine)
            columns = [col['name'] for col in inspector.get_columns('expenses')]
            
            changes_made = False
            
            # Ajouter pharmacy_id si elle n'existe pas
            if 'pharmacy_id' not in columns:
                print("Ajout de la colonne pharmacy_id a la table expenses...")
                db.session.execute(text("""
                    ALTER TABLE expenses 
                    ADD COLUMN pharmacy_id INT NULL,
                    ADD CONSTRAINT fk_expenses_pharmacy 
                    FOREIGN KEY (pharmacy_id) REFERENCES pharmacies(id)
                """))
                changes_made = True
                print("[OK] Colonne pharmacy_id ajoutee")
            else:
                print("[OK] La colonne pharmacy_id existe deja")
            
            # Ajouter notes si elle n'existe pas
            if 'notes' not in columns:
                print("Ajout de la colonne notes a la table expenses...")
                db.session.execute(text("""
                    ALTER TABLE expenses 
                    ADD COLUMN notes TEXT NULL
                """))
                changes_made = True
                print("[OK] Colonne notes ajoutee")
            else:
                print("[OK] La colonne notes existe deja")
            
            if changes_made:
                db.session.commit()
                print("\n[OK] Migration reussie : table expenses mise a jour")
            else:
                print("\n[OK] Aucune modification necessaire")
            
        except Exception as e:
            db.session.rollback()
            print(f"\n[ERREUR] Erreur lors de la migration : {e}")
            print("\nSi l'erreur persiste, executez manuellement ces commandes SQL:")
            print("ALTER TABLE expenses ADD COLUMN pharmacy_id INT NULL;")
            print("ALTER TABLE expenses ADD COLUMN notes TEXT NULL;")
            print("ALTER TABLE expenses ADD CONSTRAINT fk_expenses_pharmacy FOREIGN KEY (pharmacy_id) REFERENCES pharmacies(id);")
            raise

if __name__ == '__main__':
    migrate()


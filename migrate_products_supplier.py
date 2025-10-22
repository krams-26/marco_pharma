"""
Migration MySQL: Ajouter supplier_id a la table products
"""

from app import create_app
from app.models import db

def migrate():
    app = create_app()
    
    with app.app_context():
        try:
            # Verifier si la colonne existe deja
            from sqlalchemy import inspect, text
            inspector = inspect(db.engine)
            columns = [col['name'] for col in inspector.get_columns('products')]
            
            # Ajouter supplier_id si elle n'existe pas
            if 'supplier_id' not in columns:
                print("Ajout de la colonne supplier_id a la table products...")
                db.session.execute(text("""
                    ALTER TABLE products 
                    ADD COLUMN supplier_id INT NULL,
                    ADD CONSTRAINT fk_products_supplier 
                    FOREIGN KEY (supplier_id) REFERENCES suppliers(id)
                """))
                db.session.commit()
                print("[OK] Colonne supplier_id ajoutee")
            else:
                print("[OK] La colonne supplier_id existe deja")
            
            print("\n[OK] Migration reussie : table products mise a jour")
            
        except Exception as e:
            db.session.rollback()
            print(f"\n[ERREUR] Erreur lors de la migration : {e}")
            print("\nSi l'erreur persiste, executez manuellement cette commande SQL:")
            print("ALTER TABLE products ADD COLUMN supplier_id INT NULL;")
            print("ALTER TABLE products ADD CONSTRAINT fk_products_supplier FOREIGN KEY (supplier_id) REFERENCES suppliers(id);")
            raise

if __name__ == '__main__':
    migrate()


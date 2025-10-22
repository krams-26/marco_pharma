from app import create_app
from app.models import db

app = create_app()

with app.app_context():
    print("Suppression de toutes les tables...")
    db.drop_all()
    print("[OK] Tables supprimees")
    
    print("Creation de nouvelles tables...")
    db.create_all()
    print("[OK] Tables creees")
    
    print("\n[OK] Base de donnees reinitialisee avec succes!")


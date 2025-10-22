"""
Script de lancement de l'application Marco-Pharma
"""

from app import create_app

app = create_app()

if __name__ == '__main__':
    print("MARCO-PHARMA - SYSTEME DE GESTION DE PHARMACIE")
    print("=" * 60)
    print("JOURNAL D'ACTIVITES COMPLET")
    print("GESTION PAR LOTS AVEC FEFO")
    print("DETECTION D'ACTIVITES SUSPECTES")
    print("=" * 60)
    print()
    print("URL: http://localhost:5000")
    print("Login: admin")
    print("Mot de passe: admin123")
    print()
    print("PAGES A TESTER:")
    print("• /audits/ - Liste des activites")
    print("• /audits/dashboard - Dashboard avec graphiques")
    print("• /audits/alerts - Activites suspectes")
    print("• /stock/batches - Gestion des lots")
    print("• /pos/ - Ventes avec FEFO automatique")
    print()
    print("DONNEES DE TEST GENEREES: 98 audits")
    print()
    print("Demarrage en cours...")
    print()
    
    app.run(host='0.0.0.0', port=5000, debug=True)

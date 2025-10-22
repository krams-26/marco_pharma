"""
Point d'entrée alternatif pour Marco-Pharma
Redirige vers run.py
"""
from app import create_app

app = create_app()

if __name__ == '__main__':
    print("Demarrage de Marco-Pharma...")
    print("URL: http://localhost:5000")
    print("Login: admin / admin123")
    print()
    app.run(host='0.0.0.0', port=5000, debug=True)


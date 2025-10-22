# 🚀 Guide de Lancement - Marco Pharma

## Méthode 1 : Fichier Batch (Windows) - **RECOMMANDÉ**

Double-cliquez sur `start.bat`

Tout se fait automatiquement :
- ✅ Vérification de Python
- ✅ Installation des dépendances (uniquement si manquantes)
- ✅ Lancement de l'application
- ✅ Ouverture automatique dans le navigateur

---

## Méthode 2 : Script Python

```bash
python start.py
```

Avantages :
- Multiplateforme (Windows, Linux, Mac)
- Vérification intelligente des dépendances
- Installation automatique uniquement si nécessaire
- Messages clairs et colorés

---

## Méthode 3 : Manuelle (pour développeurs)

```bash
# 1. Installer les dépendances (une seule fois)
pip install flask flask-sqlalchemy flask-login pymysql werkzeug openpyxl

# 2. Lancer l'application
python run.py
```

---

## 🌐 Accès à l'Application

Une fois lancée, l'application est accessible sur :
- **http://localhost:5000**
- **http://127.0.0.1:5000**

---

## 👤 Comptes de Test

| Utilisateur | Mot de passe | Rôle | Description |
|------------|--------------|------|-------------|
| `admin` | `admin` | Admin | Accès complet au système |
| `manager` | `manager123` | Manager | Gestion complète de sa pharmacie |
| `pharmacien` | `pharma123` | Pharmacien | Gestion stocks et produits |
| `vendeur` | `vendeur123` | Vendeur | Créer ventes temporaires |
| `caissier` | `caissier123` | Caissier | Valider ventes et gérer caisse |

---

## ⚙️ Configuration Base de Données

La connexion MySQL est configurée dans `app/config.py` :
```python
SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root:@localhost/marphar'
```

Assurez-vous que :
- ✅ MySQL/MariaDB est démarré
- ✅ La base de données `marphar` existe
- ✅ L'utilisateur `root` a accès (sans mot de passe)

---

## 🛑 Arrêter l'Application

- Appuyez sur `Ctrl+C` dans le terminal
- Ou fermez simplement la fenêtre

---

## 📝 Notes

- Les dépendances sont installées **automatiquement** au premier lancement
- Les lancements suivants sont **instantanés** (pas de réinstallation)
- Le mode debug est activé pour le développement
- Les modifications de code sont rechargées automatiquement

---

## 🆘 Problèmes Courants

### Python non trouvé
```
Solution : Installez Python 3.8+ et ajoutez-le au PATH
```

### Port 5000 déjà utilisé
```
Solution : Modifiez le port dans run.py (ligne 6)
app.run(host='0.0.0.0', port=5001, debug=True)
```

### Erreur de connexion MySQL
```
Solution : Démarrez WAMP/XAMPP et vérifiez que MySQL est actif
```

---

**Bon développement !** 🚀


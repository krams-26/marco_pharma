# 🏥 MARCO PHARMA - Système de Gestion de Pharmacie

Application complète de gestion pour pharmacies avec support multi-sites.

## 🚀 DÉMARRAGE RAPIDE

### **Windows** (Recommandé)
Double-cliquez sur : **`LANCER_APP.bat`**

### **Tous systèmes** (Python)
```bash
python lancer.py
```

### **Manuel**
```bash
pip install -r requirements.txt
python run.py
```

---

## 📋 PRÉREQUIS

- **Python 3.8+**
- **MySQL 8.0+** (via WAMP/XAMPP)
- **Base de données** : `marphar` (créer si nécessaire)

```sql
CREATE DATABASE marphar CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

---

## 👥 COMPTES PAR DÉFAUT

| Utilisateur | Mot de passe | Rôle |
|-------------|--------------|------|
| `admin` | `admin123` | Administrateur |
| `caissier` | `caissier123` | Caissier |
| `vendeur` | `vendeur123` | Vendeur |
| `pharmacien` | `pharmacien123` | Pharmacien |

---

## ✨ FONCTIONNALITÉS

### **Gestion Complète**
- ✅ Point de Vente (POS) avec recherche rapide
- ✅ Gestion produits avec alertes stock
- ✅ Ventes et facturation
- ✅ Clients et fournisseurs
- ✅ Gestion multi-pharmacies
- ✅ Ressources humaines (RH)
- ✅ Rapports détaillés
- ✅ Audit trail complet

### **33 Modals Rapides**
- ✅ Ajouter client (POS)
- ✅ Vue rapide produit
- ✅ Détails vente
- ✅ Paiement rapide
- ✅ Créer tâche
- ✅ Modals RH (Absence, Congé, Salaire, Avance)
- ✅ ... et 24 autres !

### **Permissions Granulaires**
- ✅ 3 niveaux d'accès (Admin, Pharmacie, Personnel)
- ✅ Interface dynamique selon permissions
- ✅ Isolation des données

---

## 🛠️ OUTILS INCLUS

### **Scripts de Lancement**
- `LANCER_APP.bat` - Script Windows complet avec vérifications
- `LANCER_SIMPLE.bat` - Lancement minimal
- `lancer.py` - Script Python multi-plateforme

### **Documentation**
- `GUIDE_DEMARRAGE.md` - Guide détaillé
- `RAPPORT_FINAL_ANALYSE.md` - Rapport technique complet

---

## 📁 STRUCTURE

```
Marco-Pharma/
├── app/
│   ├── routes/          # Contrôleurs (24 blueprints)
│   ├── templates/       # Vues Jinja2
│   ├── static/          # CSS, JS, images
│   ├── models.py        # Modèles de base de données
│   └── __init__.py      # Configuration Flask
├── LANCER_APP.bat       # Script de lancement Windows
├── lancer.py            # Script de lancement Python
├── run.py               # Point d'entrée Flask
├── requirements.txt     # Dépendances Python
└── README.md            # Ce fichier
```

---

## 🔧 RÉSOLUTION DE PROBLÈMES

### **MySQL ne démarre pas**
- Démarrer WAMP/XAMPP
- Vérifier le service MySQL

### **Base 'marphar' n'existe pas**
```sql
CREATE DATABASE marphar;
```

### **Port 5000 déjà utilisé**
Modifier `run.py` ligne 6 :
```python
app.run(port=8000)  # Changer 5000 en 8000
```

### **Erreurs de dépendances**
```bash
pip install --upgrade -r requirements.txt
```

---

## 📊 TECHNOLOGIES

- **Backend** : Flask 2.3, SQLAlchemy 3.0
- **Base de données** : MySQL 8.0
- **Frontend** : Bootstrap 4 (Argon Dashboard)
- **JavaScript** : jQuery 3.6
- **Authentification** : Flask-Login
- **Exports** : Excel (openpyxl), PDF (reportlab)

---

## 📞 SUPPORT

Pour toute assistance :
1. Consulter `GUIDE_DEMARRAGE.md`
2. Vérifier `RAPPORT_FINAL_ANALYSE.md`
3. Contacter le support technique

---

## 📜 LICENCE

Propriétaire - Marco Pharma © 2025

---

**🎊 Bonne utilisation !**

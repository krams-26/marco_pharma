# 🚀 GUIDE DE DÉMARRAGE - MARCO PHARMA

## 📋 PRÉREQUIS

### **Système requis**
- **Python 3.8+** (recommandé: Python 3.11)
- **MySQL 8.0+** (via WAMP, XAMPP, ou installation directe)
- **Navigateur web** (Chrome, Firefox, Edge)

### **Base de données**
```sql
CREATE DATABASE marphar CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

## 🚀 DÉMARRAGE RAPIDE

### **Option 1: Windows (Recommandé)**
1. **Double-cliquez** sur `start.bat`
2. Le script vérifiera Python et les dépendances
3. L'application démarrera automatiquement

### **Option 2: Script Python**
```bash
python lancer.py
```

### **Option 3: Lancement manuel**
```bash
pip install -r requirements.txt
python run.py
```

## 👥 COMPTES PAR DÉFAUT

| Utilisateur | Mot de passe | Rôle |
|-------------|--------------|------|
| `admin` | `admin123` | Administrateur |
| `caissier` | `caissier123` | Caissier |
| `vendeur` | `vendeur123` | Vendeur |
| `pharmacien` | `pharmacien123` | Pharmacien |

## 🔧 RÉSOLUTION DE PROBLÈMES

### **Erreur: Python non trouvé**
- Installez Python depuis https://python.org
- Cochez "Add Python to PATH" lors de l'installation

### **Erreur: Module non trouvé**
```bash
pip install -r requirements.txt
```

### **Erreur: Base de données**
1. Démarrer MySQL (WAMP/XAMPP)
2. Créer la base `marphar`
3. Vérifier la configuration dans `app/config.py`

### **Port 5000 occupé**
Modifier `run.py` ligne 6:
```python
app.run(port=8000)  # Changer 5000 en 8000
```

## 📊 FONCTIONNALITÉS

### **Gestion Complète**
- ✅ Point de Vente (POS)
- ✅ Gestion produits et stock
- ✅ Ventes et facturation
- ✅ Clients et fournisseurs
- ✅ Multi-pharmacies
- ✅ Ressources humaines
- ✅ Rapports et audits

### **Interface Moderne**
- ✅ Design responsive
- ✅ Navigation intuitive
- ✅ Recherche rapide
- ✅ Modals dynamiques

## 🛠️ MAINTENANCE

### **Mise à jour des dépendances**
```bash
pip install --upgrade -r requirements.txt
```

### **Sauvegarde de la base**
```bash
mysqldump -u root -p marphar > backup.sql
```

### **Restauration**
```bash
mysql -u root -p marphar < backup.sql
```

## 📞 SUPPORT

Pour toute assistance :
1. Vérifier ce guide
2. Consulter les logs d'erreur
3. Contacter le support technique

---

**🎊 Bonne utilisation de Marco Pharma !**

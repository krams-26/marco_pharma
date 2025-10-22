# 🚀 GUIDE DE DÉMARRAGE - MARCO PHARMA

## ⚡ **LANCEMENT RAPIDE (1 clic)**

### **Windows**
Double-cliquez sur : **`LANCER_APP.bat`**

L'application va :
1. Vérifier Python
2. Vérifier MySQL
3. Installer les dépendances
4. Lancer l'application
5. Ouvrir le navigateur automatiquement

---

## 📋 **PRÉREQUIS**

### **Obligatoires**
- ✅ **Python 3.8+** - [Télécharger](https://www.python.org/downloads/)
- ✅ **MySQL 8.0+** - Via WAMP/XAMPP
- ✅ **Base de données** : `marphar` (doit exister)

### **Optionnels**
- Git (pour le versionnement)
- Visual Studio Code (pour l'édition)

---

## 🔧 **INSTALLATION MANUELLE**

### **Étape 1: Créer la base de données**
```sql
CREATE DATABASE marphar CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### **Étape 2: Installer les dépendances**
```bash
pip install -r requirements.txt
```

### **Étape 3: Lancer l'application**
```bash
python run.py
```

### **Étape 4: Accéder à l'application**
Ouvrez votre navigateur : **http://localhost:5000**

---

## 👥 **COMPTES PAR DÉFAUT**

| Utilisateur | Mot de passe | Rôle | Permissions |
|-------------|--------------|------|-------------|
| `admin` | `admin123` | Administrateur | Toutes |
| `caissier` | `caissier123` | Caissier | Ventes, Caisse |
| `vendeur` | `vendeur123` | Vendeur | POS uniquement |
| `pharmacien` | `pharmacien123` | Pharmacien | Produits, Stock |
| `manager` | `manager123` | Manager | Vue pharmacie |

---

## 🛠️ **OUTILS DE DIAGNOSTIC**

### **Test Complet**
```bash
python diagnostic_approfondi.py
```

### **Test d'Intégration**
```bash
python test_integration_final.py
```

### **Vérifier les Routes**
```bash
python -c "from app import create_app; app=create_app(); print([str(r) for r in app.url_map.iter_rules()])"
```

---

## ❌ **RÉSOLUTION DE PROBLÈMES**

### **Erreur: "MySQL ne démarre pas"**
```bash
# Démarrer WAMP/XAMPP
# Vérifier que le service MySQL est en cours d'exécution
```

### **Erreur: "Base de données 'marphar' n'existe pas"**
```sql
-- Via phpMyAdmin ou ligne de commande MySQL
CREATE DATABASE marphar;
```

### **Erreur: "Module 'flask' not found"**
```bash
pip install -r requirements.txt
```

### **Erreur: "Port 5000 déjà utilisé"**
Modifier `run.py` ligne 6 :
```python
app.run(host='0.0.0.0', port=8000, debug=True)  # Utiliser port 8000
```

---

## 📱 **URLS IMPORTANTES**

| Page | URL |
|------|-----|
| Connexion | http://localhost:5000/login |
| Dashboard | http://localhost:5000/dashboard |
| Point de Vente | http://localhost:5000/pos |
| Produits | http://localhost:5000/products |
| Ventes | http://localhost:5000/sales |
| Clients | http://localhost:5000/customers |
| RH | http://localhost:5000/hr |

---

## 🎯 **FONCTIONNALITÉS CLÉS**

### **33 Modals Opérationnels**
- ✅ Ajouter client rapide (POS)
- ✅ Vue rapide produit
- ✅ Détails vente
- ✅ Paiement rapide
- ✅ Créer tâche (navbar)
- ✅ 4 modals RH (Absence, Congé, Salaire, Avance)
- ✅ ... et 24 autres !

### **Gestion Multi-Pharmacies**
- ✅ Dépôt central
- ✅ Pharmacies multiples
- ✅ Transferts inter-pharmacies
- ✅ Isolation des données

### **Permissions Granulaires**
- ✅ Par module
- ✅ Par action
- ✅ Interface dynamique
- ✅ 3 niveaux d'accès (Admin, Pharmacie, Personnel)

---

## 📞 **SUPPORT**

### **En cas de problème**
1. Lancer le diagnostic : `python diagnostic_approfondi.py`
2. Vérifier les logs dans le terminal
3. Consulter `RAPPORT_FINAL_ANALYSE.md`
4. Contacter le support technique

---

## 🎓 **FORMATION**

### **Premiers Pas**
1. Se connecter avec `admin/admin123`
2. Créer une pharmacie (Paramètres → Pharmacies)
3. Créer des utilisateurs (Utilisateurs)
4. Ajouter des produits (Produits)
5. Tester le POS (Point de Vente)

### **Tests Recommandés**
- ✅ Créer une vente dans le POS
- ✅ Tester les modals rapides
- ✅ Vérifier les permissions
- ✅ Enregistrer une absence
- ✅ Créer une tâche

---

**🎊 L'APPLICATION EST PRÊTE !**

Double-cliquez sur `LANCER_APP.bat` pour commencer !


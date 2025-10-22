# 🚀 INSTRUCTIONS FINALES - MARCO PHARMA

## ⚡ **LANCEMENT IMMÉDIAT** (1 clic)

### **👉 Double-cliquez sur : `LANCER.bat`**

C'est tout ! L'application va :
1. ✅ Installer les dépendances nécessaires
2. ✅ Ouvrir le navigateur automatiquement
3. ✅ Démarrer sur http://localhost:5000

---

## 🔑 **CONNEXION**

```
URL: http://localhost:5000
Login: admin
Mot de passe: admin123
```

---

## 📂 **SCRIPTS DISPONIBLES**

| Fichier | Type | Recommandation |
|---------|------|----------------|
| **LANCER.bat** | Windows | ⭐ **UTILISEZ CELUI-CI** |
| LANCER_SIMPLE.bat | Windows | Alternative simple |
| DEMARRER.bat | Windows | Alternative |
| lancer.py | Python | Multiplateforme |
| run.py | Python | Manuel |

---

## ❓ **POURQUOI LANCER_APP.bat SE BLOQUAIT ?**

`LANCER_APP.bat` contient une commande `choice` qui attend une réponse utilisateur :

```batch
choice /C ON /N /M ">"  ← Attend O ou N
if errorlevel 2 exit /b 1
```

**Solution** : Le nouveau `LANCER.bat` **ne pose pas de questions** et lance directement !

---

## 🛠️ **EN CAS DE PROBLÈME**

### **Si l'application ne démarre pas :**

#### **1. Vérifier MySQL**
```
→ Ouvrir WAMP/XAMPP
→ Démarrer le service MySQL (icône verte)
→ Vérifier que la base 'marphar' existe
```

#### **2. Installer manuellement les dépendances**
```bash
pip install Flask Flask-SQLAlchemy Flask-Login PyMySQL Werkzeug
```

#### **3. Lancer manuellement**
```bash
python run.py
```

Puis ouvrir : **http://localhost:5000**

---

## ✅ **VÉRIFICATION RAPIDE**

Pour tester si tout fonctionne :

```bash
python -c "from app import create_app; app=create_app(); print('✓ OK')"
```

Si cela affiche `✓ OK`, l'application peut démarrer.

---

## 🎯 **APRÈS LE LANCEMENT**

### **Tester les Modals :**

1. **Aller sur http://localhost:5000/pos**
   - Cliquer "Nouveau client" → Modal s'ouvre ✓

2. **Aller sur http://localhost:5000/products**
   - Cliquer icône 👓 sur un produit → Détails ✓

3. **Aller sur http://localhost:5000/sales**
   - Cliquer 👁️ sur une vente → Détails ✓

4. **Dans la navbar (en haut)**
   - Cliquer "Nouvelle tâche" → Modal ✓

5. **Aller sur http://localhost:5000/hr/absences**
   - Cliquer "Enregistrer une Absence" → Modal ✓

---

## 📞 **COMPTES DE TEST**

| Utilisateur | Mot de passe | Rôle | Permissions |
|-------------|--------------|------|-------------|
| `admin` | `admin123` | Admin | Toutes |
| `caissier` | `caissier123` | Caissier | Ventes, Caisse, Validation |
| `vendeur` | `vendeur123` | Vendeur | POS uniquement |
| `pharmacien` | `pharmacien123` | Pharmacien | Produits, Stock |
| `manager` | `manager123` | Manager | Sa pharmacie |

---

## 🎊 **RÉSUMÉ**

### **✅ POUR LANCER :**
👉 **Double-clic sur `LANCER.bat`**

### **✅ POUR TESTER :**
👉 **Ouvrir http://localhost:5000**

### **✅ POUR SE CONNECTER :**
👉 **admin / admin123**

---

## 📋 **FICHIERS CRÉÉS POUR VOUS**

- ✅ `LANCER.bat` - Script de lancement simple
- ✅ `GUIDE_DEMARRAGE.md` - Guide complet
- ✅ `README.md` - Documentation
- ✅ `SOLUTION_LANCEMENT.txt` - Solution au blocage
- ✅ `INSTRUCTIONS_FINALES.md` - Ce fichier

---

**🎯 TOUT EST PRÊT ! DOUBLE-CLIQUEZ SUR `LANCER.bat` MAINTENANT !** 🚀



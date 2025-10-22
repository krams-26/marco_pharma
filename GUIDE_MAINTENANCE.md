# Guide de Maintenance - Marco-Pharma

## ✅ Problème Résolu: Erreur 405 après Connexion

### Qu'est-ce qui s'est passé?

L'erreur **405 "Method Not Allowed"** après la connexion était causée par une **incompatibilité entre la structure de la base de données et les modèles de l'application**.

**Cause technique:**
- Les modèles Python ont été mis à jour avec de nouvelles colonnes et relations
- La base de données SQLite contenait l'ancienne structure
- L'application ne pouvait pas démarrer correctement à cause de ces incohérences

### Solution Appliquée

1. ✅ Arrêt de l'application
2. ✅ Réinitialisation complète de la base de données
3. ✅ Recréation avec la nouvelle structure
4. ✅ Réajout des données de test
5. ✅ Redémarrage de l'application

---

## 🚀 L'Application est Maintenant Fonctionnelle

**URL:** http://localhost:5000

**Identifiants Admin:**
- Username: `admin`
- Password: `admin123`

---

## 🔧 Comment Éviter ce Problème à l'Avenir

### Règle Importante

**Chaque fois que vous modifiez `app/models.py`, réinitialisez la base de données:**

```bash
# 1. Arrêter l'application (Ctrl+C)

# 2. Réinitialiser la base de données
python reset_db.py

# 3. Rajouter les données de test
python seed_data.py

# 4. Redémarrer l'application
python run.py
```

**OU utilisez le script automatique:**
```bash
reinitialiser.bat
```

---

## 📋 Scripts Disponibles

### `start.bat`
Démarre l'application (vérifie si la base de données existe)

### `reinitialiser.bat`
Réinitialise complètement la base de données et rajoute les données de test

### `ouvrir_app.bat`
Ouvre l'application dans le navigateur

### Scripts Python

#### `reset_db.py`
Supprime et recrée toutes les tables de la base de données
```bash
python reset_db.py
```

#### `seed_data.py`
Ajoute les données de test (pharmacies, produits, clients, etc.)
```bash
python seed_data.py
```

#### `run.py`
Lance l'application Flask
```bash
python run.py
```

---

## 🔍 Diagnostic des Problèmes Courants

### Problème: Erreur 405 après connexion
**Solution:** Réinitialisez la base de données
```bash
python reset_db.py
python seed_data.py
```

### Problème: Erreur "no such column"
**Cause:** Structure de base de données obsolète  
**Solution:** Réinitialisez la base de données
```bash
python reset_db.py
python seed_data.py
```

### Problème: Erreur "SalePayment not found"
**Cause:** Relations manquantes dans la base de données  
**Solution:** Réinitialisez la base de données
```bash
python reset_db.py
python seed_data.py
```

### Problème: Page blanche ou erreur 500
**Solution:** 
1. Vérifiez les logs dans le terminal
2. Réinitialisez la base de données
3. Vérifiez que toutes les dépendances sont installées

### Problème: Port 5000 déjà utilisé
**Solution:** Modifiez le port dans `run.py`
```python
app.run(host='0.0.0.0', port=5001, debug=True)
```

---

## 📊 Données de Test Incluses

Après exécution de `seed_data.py`, vous aurez:

### Utilisateurs (4)
- **admin** / admin123 (Administrateur)
- **vendeur1** / vendeur123 (Vendeur)
- **gestionnaire** / manager123 (Gestionnaire)
- **pharmacien** / pharma123 (Pharmacien)

### Pharmacies (4)
1. Pharmacie MARCOPHAR Centrale (Dépôt)
2. Pharmacie MARCOPHAR Nord
3. Pharmacie MARCOPHAR Sud
4. Pharmacie MARCOPHAR Est

### Produits (15)
Médicaments variés avec stocks et prix

### Clients (8)
- 4 Grossistes (hôpitaux, cliniques)
- 3 Clients réguliers
- 1 Client VIP

### Autres Données
- 5 Ventes de démonstration
- 2 Employés
- Transactions de caisse
- Taux de change

---

## 🔄 Workflow de Développement Recommandé

### Quand modifier les modèles:

1. **Modifier** `app/models.py`
2. **Sauvegarder** les changements
3. **Arrêter** l'application (Ctrl+C)
4. **Réinitialiser** la base de données:
   ```bash
   python reset_db.py
   python seed_data.py
   ```
5. **Redémarrer** l'application:
   ```bash
   python run.py
   ```

### Alternative avec migrations (Pour production):

Pour éviter de perdre les données en production, utilisez Flask-Migrate:

```bash
# Initialiser les migrations (une seule fois)
flask db init

# Créer une migration après modification des modèles
flask db migrate -m "Description des changements"

# Appliquer la migration
flask db upgrade
```

---

## 🛠️ Configuration de la Base de Données

### SQLite (Par défaut - Développement)
```python
# app/config.py
SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, '..', 'instance', 'pharmacy.db')
```

### MySQL (Production)
```python
# app/config.py
SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://user:password@localhost/marphar'
```

---

## 📝 Fichiers Importants

### Configuration
- `app/config.py` - Configuration de l'application
- `app/models.py` - Modèles de données (⚠️ Réinitialiser la DB après modification)
- `app/decorators.py` - Décorateurs de permissions

### Scripts
- `run.py` - Point d'entrée de l'application
- `reset_db.py` - Réinitialisation de la DB
- `seed_data.py` - Données de test
- `start.bat` - Démarrage automatique
- `reinitialiser.bat` - Réinitialisation automatique

### Documentation
- `README.md` - Documentation complète
- `INSTRUCTIONS_DEMARRAGE.md` - Instructions de démarrage
- `PROBLEME_RESOLU.txt` - Résolution du problème 405
- `GUIDE_MAINTENANCE.md` - Ce guide

---

## ⚠️ Notes Importantes

1. **Développement:** Utilisez SQLite (configuration actuelle)
2. **Production:** Passez à MySQL et utilisez les migrations
3. **Sécurité:** Changez SECRET_KEY et les mots de passe en production
4. **Performances:** Désactivez DEBUG en production
5. **Serveur:** Utilisez Gunicorn + Nginx en production

---

## 📞 En Cas de Problème

1. **Consultez ce guide** pour les solutions courantes
2. **Vérifiez les logs** dans le terminal
3. **Réinitialisez la base de données** si nécessaire
4. **Vérifiez les dépendances:** `pip install -r requirements.txt`

---

**L'application fonctionne maintenant parfaitement!** 🎉

Connectez-vous avec **admin/admin123** pour commencer.


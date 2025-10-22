# Instructions de Démarrage - Marco-Pharma

## ✅ Application Lancée avec Succès!

L'application est actuellement accessible à l'adresse suivante:

**URL**: http://localhost:5000

## 📝 Comptes de Test Disponibles

### Compte Administrateur
- **Username**: `admin`
- **Password**: `admin123`
- **Permissions**: Accès complet à toutes les fonctionnalités

### Compte Vendeur
- **Username**: `vendeur1` ou `vendeur2`
- **Password**: `vendeur123`
- **Permissions**: Ventes et consultation des rapports

### Compte Gestionnaire
- **Username**: `gestionnaire`
- **Password**: `manager123`
- **Permissions**: Gestion des produits, stocks, clients, paiements

### Compte Pharmacien
- **Username**: `pharmacien`
- **Password**: `pharma123`
- **Permissions**: Gestion des produits, ventes et stocks

## 📊 Données de Test Créées

### Pharmacies (4)
1. **Pharmacie MARCOPHAR Centrale** (Dépôt Central)
2. **Pharmacie MARCOPHAR Nord**
3. **Pharmacie MARCOPHAR Sud**
4. **Pharmacie MARCOPHAR Est**

### Produits (15)
- Paracétamol 500mg
- Amoxicilline 500mg
- Quinine 300mg
- Amlodipine 5mg
- Aspirine 100mg
- Ciprofloxacine 500mg
- Artéméther-Luméfantrine
- Metformine 850mg
- Ibuprofène 400mg
- Complexe Vitamine B
- Vitamine C 1000mg
- Alcool 70%
- Bétadine Solution
- Diclofénac 50mg
- Oméprazole 20mg

### Clients (8)
- 4 clients grossistes (Hôpitaux et cliniques)
- 3 clients réguliers
- 1 client VIP

### Ventes (5)
- 5 ventes de test avec différents produits et clients

### Autres Données
- Employés (2)
- Transactions de caisse (7)
- Taux de change (3)

## 🚀 Comment Démarrer l'Application

### Méthode 1: Script Automatique
```bash
start.bat
```

### Méthode 2: Manuel
```bash
# 1. Installer les dépendances
pip install -r requirements.txt

# 2. Si besoin de réinitialiser la base de données
python reset_db.py

# 3. Ajouter les données de test (optionnel)
python seed_data.py

# 4. Lancer l'application
python run.py
```

## 🔄 Commandes Utiles

### Réinitialiser la Base de Données
```bash
python reset_db.py
```

### Ajouter des Données de Test
```bash
python seed_data.py
```

### Lancer l'Application
```bash
python run.py
```

## 📂 Structure de l'Application

### Modules Principaux
1. **Dashboard** - Vue d'ensemble et statistiques
2. **POS (Point de Vente)** - Interface de vente rapide
3. **Produits** - Gestion du catalogue
4. **Stock** - Gestion des mouvements et inventaire
5. **Clients** - Gestion des clients et crédits
6. **Ventes** - Historique et détails des ventes
7. **Ressources Humaines** - Employés, absences, congés, salaires
8. **Caisse** - Transactions, entrées et sorties
9. **Pharmacies** - Gestion multi-sites
10. **Paiements** - Gestion des paiements clients
11. **Proformas** - Factures proforma
12. **Rapports** - Statistiques et analyses
13. **Paramètres** - Configuration et taux de change
14. **Audits** - Journal d'activité

### Pages Disponibles
- **/login** - Page de connexion
- **/dashboard** - Tableau de bord (nécessite authentification)
- **/pos** - Point de vente
- **/products** - Liste des produits
- **/customers** - Liste des clients
- **/sales** - Historique des ventes
- **/stock** - Gestion du stock
- **/hr** - Ressources humaines
- **/cashier** - Caisse
- **/pharmacies** - Gestion des pharmacies
- **/payments** - Paiements
- **/proforma** - Factures proforma
- **/reports** - Rapports
- **/settings** - Paramètres
- **/audits** - Audits

## ⚙️ Configuration

### Base de Données
- **Type**: SQLite (pour développement)
- **Emplacement**: `instance/pharmacy.db`
- **Pour passer à MySQL**: Modifiez `app/config.py`

### Fichiers de Configuration
- `app/config.py` - Configuration principale
- `requirements.txt` - Dépendances Python

## 🔒 Sécurité

⚠️ **IMPORTANT pour la production**:
1. Changez `SECRET_KEY` dans `app/config.py`
2. Désactivez le mode DEBUG
3. Changez tous les mots de passe par défaut
4. Configurez HTTPS
5. Utilisez un serveur de production (Gunicorn + Nginx)

## 🆘 Dépannage

### L'application ne démarre pas
- Vérifiez que Python 3.8+ est installé
- Vérifiez que toutes les dépendances sont installées: `pip install -r requirements.txt`

### Erreur de base de données
- Réinitialisez la base de données: `python reset_db.py`
- Recréez les données de test: `python seed_data.py`

### Port 5000 déjà utilisé
Modifiez le port dans `run.py`:
```python
app.run(host='0.0.0.0', port=5001, debug=True)
```

### Erreur 404 sur les pages
- Vérifiez que vous êtes connecté
- Certaines pages nécessitent des permissions spécifiques

## 📞 Support

Pour toute question ou problème, consultez:
- Le fichier `README.md` pour plus de détails
- Les logs de l'application dans le terminal
- La documentation Flask: https://flask.palletsprojects.com/

---

**Bon développement avec Marco-Pharma! 🏥💊**


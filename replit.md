# Pharmacie Moderne - Système de Gestion de Pharmacie

## Vue d'ensemble

Application web complète de gestion de pharmacie développée avec Flask et Bootstrap 5. Le système offre une gestion complète des opérations d'une pharmacie moderne avec des fonctionnalités avancées de point de vente, gestion de stock, RH, et rapports.

## Dernières modifications

**Date:** 14 octobre 2025

### Corrections critiques appliquées
- ✅ Système de permissions granulaires entièrement appliqué avec décorateur `require_permission`
- ✅ Page 403 personnalisée pour accès refusé (évite boucles de redirection infinies)
- ✅ Correction clés étrangères avec `db.session.flush()` avant création objets dépendants
- ✅ Toutes les routes sensibles protégées par permissions appropriées

### Architecture complète implémentée
- Backend Flask avec SQLAlchemy (SQLite)
- Frontend Bootstrap 5 responsive
- Système d'authentification avec Flask-Login
- Système de permissions granulaires entièrement fonctionnel
- 13 modules fonctionnels complets et sécurisés

### Stack Technologique

**Backend:**
- Flask 3.1.2 (framework web)
- Flask-SQLAlchemy 3.1.1 (ORM)
- Flask-Login 0.6.3 (authentification)
- Flask-Migrate 4.1.0 (migrations DB)
- Flask-WTF 1.2.2 (formulaires)
- Werkzeug 3.1.3 (sécurité)

**Frontend:**
- Bootstrap 5.3.0 (UI framework)
- Bootstrap Icons 1.11.0
- jQuery 3.7.0

**Outils:**
- ReportLab 4.4.4 (génération PDF)
- OpenPyXL 3.1.5 (export Excel)
- python-barcode 0.16.1 (codes-barres)
- Pillow 11.3.0 (images)

## Modules Implémentés

### 1. Authentification & Sécurité
- Système de connexion sécurisé
- Décorateur de permissions `require_permission` appliqué à toutes les routes
- Page 403 personnalisée pour accès refusé
- Système de permissions granulaires personnalisables par utilisateur
- 12 permissions individuelles assignables par utilisateur
- 5 rôles prédéfinis: Admin, Manager, Pharmacien, Caissier, Vendeur
- Audit complet de toutes les activités

### 2. Tableau de bord
- Statistiques en temps réel
- Alertes de stock faible
- Produits expirés
- Ventes du jour/mois
- Liste des ventes récentes

### 3. Point de Vente (POS)
- Interface intuitive de vente
- Recherche produits par nom/code-barres
- Gestion des paiements partiels
- Impression de factures
- Support multi-clients (anonyme/enregistré)

### 4. Gestion des Produits
- Catalogue complet
- Codes-barres
- Prix d'achat/vente/gros
- Gestion des stocks
- Alertes expiration/stock faible
- Catégorisation

### 5. Gestion des Clients
- Clients réguliers et grossistes
- Historique des achats
- Gestion des crédits
- Limites de crédit

### 6. Ventes
- Historique complet
- Détails des factures
- Recherche par numéro de facture
- Statuts de paiement

### 7. Gestion des Utilisateurs
- Création d'utilisateurs
- Attribution de rôles
- Permissions personnalisées individuellement
- Activation/désactivation

### 8. Gestion du Stock
- Mouvements d'inventaire (entrées/sorties)
- Gestion des lots (batches)
- Traçabilité complète
- Ajustements manuels

### 9. Personnel RH
- Gestion des absences
- Paiements de salaires
- Demandes de congé (approbation/rejet)
- Demandes de crédit employés

### 10. Gestion des Paiements
- Suivi des paiements
- Paiements en attente
- Historique des transactions
- Multi-méthodes (espèces, carte, mobile money, virement)

### 11. Caisse
- Gestion de la caisse journalière
- Entrées/sorties
- Rapprochement
- Historique des transactions

### 12. Rapports
- Rapports de ventes (quotidiens/mensuels)
- Rapports de dépenses
- Rapports de stock
- Rapports clients
- Exports PDF/Excel prévus

### 13. Audits
- Logging complet de toutes les activités
- Traçabilité utilisateur
- Historique des modifications
- Filtres par utilisateur/action/date

### 14. Paramètres
- Informations générales de l'entreprise
- Taux de change manuels
- Configuration du système
- Gestion des devises

## Structure du Projet

```
/
├── app/
│   ├── __init__.py           # Initialisation Flask
│   ├── config.py             # Configuration
│   ├── models.py             # Modèles SQLAlchemy
│   ├── routes/              # Blueprints
│   │   ├── auth.py
│   │   ├── dashboard.py
│   │   ├── pos.py
│   │   ├── products.py
│   │   ├── customers.py
│   │   ├── sales.py
│   │   ├── users.py
│   │   ├── stock.py
│   │   ├── hr.py
│   │   ├── payments.py
│   │   ├── cashier.py
│   │   ├── reports.py
│   │   ├── audits.py
│   │   └── settings.py
│   ├── templates/           # Templates Jinja2
│   └── static/             # CSS, JS, images
├── run.py                   # Point d'entrée
└── pharmacy.db             # Base de données SQLite
```

## Modèles de Données

### Principaux modèles:
- **User**: Utilisateurs et authentification
- **Product**: Produits et médicaments
- **ProductBatch**: Lots de produits
- **Customer**: Clients
- **Sale**: Ventes
- **SaleItem**: Lignes de vente
- **Payment**: Paiements
- **StockMovement**: Mouvements de stock
- **Employee**: Employés
- **Absence**: Absences
- **SalaryPayment**: Paiements salaires
- **LeaveRequest**: Demandes de congé
- **CreditRequest**: Demandes de crédit
- **CashTransaction**: Transactions caisse
- **Expense**: Dépenses
- **Audit**: Audits
- **Setting**: Paramètres
- **ExchangeRate**: Taux de change

## Système de Permissions

Le système utilise un modèle de permissions granulaires où:
- Chaque utilisateur a un **rôle** (point de départ)
- Chaque utilisateur peut avoir des **permissions individuelles** différentes de son rôle
- Les permissions sont stockées en JSON dans le profil utilisateur
- 12 permissions disponibles pour contrôle d'accès fin

### Permissions disponibles:
- view_dashboard
- manage_products
- manage_sales
- manage_customers
- manage_users
- manage_stock
- manage_hr
- manage_payments
- manage_cashier
- view_reports
- view_audits
- manage_settings

## Identifiants par Défaut

**Administrateur:**
- Username: `admin`
- Password: `admin123`

## Démarrage de l'Application

```bash
python run.py
```

L'application sera accessible sur: http://0.0.0.0:5000

## Fonctionnalités Clés

### 1. Point de Vente
- Recherche rapide de produits
- Panier interactif
- Calcul automatique des totaux
- Gestion des remises
- Paiements partiels
- Impression de factures

### 2. Gestion du Stock
- Alertes automatiques de stock faible
- Alertes de produits expirés
- Traçabilité complète (lots, mouvements)
- Ajustements d'inventaire

### 3. Système RH Complet
- Gestion des absences
- Paiements de salaires avec historique
- Système de demandes de congé (workflow approbation)
- Demandes de crédit employés

### 4. Rapports et Analytics
- Tableaux de bord avec statistiques temps réel
- Rapports de ventes par période
- Analyse des performances
- Rapports clients

### 5. Audit et Sécurité
- Logging automatique de toutes les actions
- Traçabilité complète
- Gestion des sessions
- Permissions granulaires

## Notes Techniques

### Base de Données
- SQLite pour le développement
- Migration facile vers PostgreSQL en production
- Migrations automatiques avec Flask-Migrate

### Sécurité
- Mots de passe hachés avec Werkzeug
- Protection CSRF avec Flask-WTF
- Sessions sécurisées
- Audit trail complet

### Performance
- Pagination sur toutes les listes
- Requêtes optimisées avec SQLAlchemy
- Chargement lazy des relations

## Développements Futurs

### Prévus:
- Export PDF/Excel des rapports
- Graphiques de ventes avec Chart.js
- Notifications par email/SMS
- API REST pour intégrations
- Application mobile
- Multi-devises avec conversion automatique
- Support des codes-barres avec scanner

## Préférences Utilisateur

- Interface en français
- Design responsive Bootstrap 5
- Architecture modulaire avec Blueprints
- Code commenté et structuré
- Patterns MVC respectés

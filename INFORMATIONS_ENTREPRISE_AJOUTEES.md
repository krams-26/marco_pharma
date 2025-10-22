# ✅ Informations de l'Entreprise Ajoutées

## 📋 Ce qui a été fait

### 1. ✅ **Informations de Base** (Option 1)
Ajouté dans `app/config.py`:
- **Nom**: MARCO PHARMA SARL
- **Type juridique**: SARL
- **Secteur**: Pharmacie / Distribution pharmaceutique
- **Description**: Entreprise spécialisée dans la distribution de produits pharmaceutiques
- **Année de création**: 2020
- **Statut légal**: Société à Responsabilité Limitée

### 2. ✅ **Coordonnées de Contact** (Option 2)
Ajouté dans `app/config.py`:
- **Email**: contact@marco-pharma.com
- **Téléphone**: +33 1 23 45 67 89
- **Site web**: https://marco-pharma.com
- **Adresse complète**: 123 Rue de la Pharmacie, 75001 Paris, France
  - Rue: 123 Rue de la Pharmacie
  - Code postal: 75001
  - Ville: Paris
  - Pays: France

### 3. ✅ **Informations Légales** (Option 3)
Ajouté dans `app/config.py` (valeurs vides à compléter):
- **RCCM**: '' (À compléter)
- **Numéro d'identification nationale**: '' (À compléter)
- **Numéro fiscal**: '' (À compléter)
- **Numéro de TVA**: '' (À compléter)
- **Date d'immatriculation**: '' (À compléter)
- **Représentant légal**: '' (À compléter)

### 4. ✅ **Logo corrigé**
- Logo copié depuis PharmaStock: `marco-pharma-logo.png`
- Chemin mis à jour dans `sidenav.html`
- Logo maintenant visible dans la sidebar

## 📂 Fichiers modifiés

1. **app/config.py**
   - Ajout des 3 sections d'informations de l'entreprise
   - Ajout des paramètres financiers
   - Ajout des paramètres de stock
   - Ajout des paramètres régionaux

2. **app/templates/includes/sidenav.html**
   - Correction du chemin du logo
   - Logo: `static/img/marco-pharma-logo.png`

3. **app/static/img/marco-pharma-logo.png**
   - Logo copié depuis PharmaStock

## 🔧 Paramètres additionnels ajoutés

### Paramètres Financiers
- Devise principale: USD
- Devise secondaire: CDF
- Taux de change: 1 USD = 3100 CDF
- Taux de TVA: 18%
- Marge minimale: 20%

### Paramètres de Stock
- Seuil de stock faible: 10 unités
- Seuil de rupture: 5 unités
- Alerte d'expiration: 30 jours
- Marge de sécurité: 15%

### Paramètres Régionaux
- Fuseau horaire: Europe/Paris
- Langue: Français (fr)
- Format de date: d/m/Y
- Format d'heure: H:i

## 📝 Utilisation dans l'application

Ces informations sont maintenant accessibles via:

```python
from flask import current_app

# Informations de base
nom_entreprise = current_app.config['COMPANY_NAME']
type_entreprise = current_app.config['COMPANY_TYPE']
secteur = current_app.config['COMPANY_SECTOR']

# Coordonnées
email = current_app.config['COMPANY_EMAIL']
phone = current_app.config['COMPANY_PHONE']
website = current_app.config['COMPANY_WEBSITE']
adresse = current_app.config['COMPANY_ADDRESS']

# Informations légales
rccm = current_app.config['COMPANY_RCCM']
vat_number = current_app.config['COMPANY_VAT_NUMBER']

# Paramètres financiers
devise = current_app.config['CURRENCY_CODE']
taux_change = current_app.config['EXCHANGE_RATE']
tva = current_app.config['TVA_RATE']
```

## 🎯 Prochaines étapes recommandées

1. **Compléter les informations légales** dans `app/config.py`:
   - RCCM
   - Numéros d'identification
   - Date d'immatriculation
   - Représentant légal

2. **Créer une page de paramètres** pour modifier ces informations via l'interface

3. **Utiliser ces informations** dans:
   - Les factures
   - Les rapports
   - Le footer de l'application
   - Les emails

## ✅ Statut Final

- ✅ Option 1 (Informations de base): **AJOUTÉE**
- ✅ Option 2 (Coordonnées): **AJOUTÉE**
- ✅ Option 3 (Informations légales): **AJOUTÉE** (à compléter)
- ✅ Logo de la sidebar: **CORRIGÉ**

---

**Source des données**: PharmaStock-CI4 (C:\wamp64\www\PharmaStock-CI4\app\Config\CompanyConfig.php)


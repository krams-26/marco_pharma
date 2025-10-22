# Plan d'Implémentation - Modules Existants Marco-Pharma

## 🎯 ANALYSE COMPLÈTE : OÙ IMPLÉMENTER LES FONCTIONNALITÉS

---

## ✅ BONNE NOUVELLE : LA PLUPART DES STRUCTURES EXISTENT DÉJÀ!

### Modules et Tables Actuels:
1. ✅ **ProductBatch** - Table existe (ligne 137 models.py)
2. ✅ **StockMovement** - Table existe (ligne 263 models.py)
3. ✅ **Audit** - Table existe (ligne 379 models.py)
4. ✅ **TempSale** - Table existe! (ligne 665 models.py)
5. ✅ **Routes Stock** - `app/routes/stock.py` existe
6. ✅ **Routes Audits** - `app/routes/audits.py` existe
7. ✅ **Routes Sales** - Gère déjà TempSale (lignes 309-410)

---

## 📋 ÉTAT ACTUEL VS FONCTIONNALITÉS MANQUANTES

### 1️⃣ GESTION PAR LOTS (Stock Lots)

#### ✅ CE QUI EXISTE DÉJÀ:

**Table `ProductBatch` (models.py:137-149)**:
```python
class ProductBatch(db.Model):
    id, product_id, batch_number, quantity, purchase_price
    expiry_date, received_date, supplier, is_active
```

**Routes Existantes** (`app/routes/stock.py`):
- `/stock/batches` - Liste des lots (ligne 121)
- `/stock/add-batch` - Ajouter lot (ligne 134)

**Templates Existants**:
- `app/templates/stock/batches.html` - Affichage lots
- `app/templates/stock/add_batch.html` - Formulaire ajout

#### ❌ CE QUI MANQUE:

1. **Champs Manquants dans ProductBatch**:
   - ❌ `pharmacy_id` (pour multi-pharmacies)
   - ❌ `initial_quantity` (quantité initiale)
   - ❌ `manufacture_date` (date fabrication)
   - ❌ `status` (active, expired, recalled, depleted)
   - ❌ `unit_cost` (coût unitaire)

2. **Table `batch_movements` (Traçabilité par lot)**:
   - ❌ Nouvelle table pour mouvements par lot
   - ❌ Types: entry, sale, transfer, adjustment, expiry
   - ❌ Lien avec lot_id, user_id, reference

3. **Fonctionnalités Routes**:
   - ❌ Édition de lot (`/stock/batches/<id>/edit`)
   - ❌ Vue détaillée lot (`/stock/batches/<id>`)
   - ❌ Historique par lot (`/stock/batches/<id>/movements`)
   - ❌ Alertes expiration (`/stock/batches/expiring`)
   - ❌ Export lots (`/stock/batches/export`)
   - ❌ Sélection FEFO dans POS

4. **Templates Manquants**:
   - ❌ `stock/batch_view.html` - Détails + historique
   - ❌ `stock/batch_edit.html` - Éditer lot
   - ❌ `stock/batch_alerts.html` - Lots expirant
   - ❌ Améliorer `stock/batches.html` - Filtres, pagination, statuts

5. **Logique POS**:
   - ❌ Sélection automatique FEFO lors de vente
   - ❌ Déduction stock du bon lot
   - ❌ Blocage lots expirés

#### 📍 OÙ IMPLÉMENTER:

**Fichiers à Modifier**:
```
1. app/models.py (ligne 137-149)
   ➡️ Ajouter champs manquants à ProductBatch
   ➡️ Créer nouvelle classe BatchMovement

2. app/routes/stock.py
   ➡️ Enrichir route /batches (filtres, pagination)
   ➡️ Ajouter /batches/<id> (vue détaillée)
   ➡️ Ajouter /batches/<id>/edit
   ➡️ Ajouter /batches/<id>/movements
   ➡️ Ajouter /batches/expiring (alertes)
   ➡️ Ajouter /batches/export

3. app/routes/pos.py
   ➡️ Modifier logique vente (ligne 88-108)
   ➡️ Ajouter sélection FEFO automatique
   ➡️ Déduire du bon lot

4. app/templates/stock/
   ➡️ Enrichir batches.html (filtres, statuts, actions)
   ➡️ Créer batch_view.html
   ➡️ Créer batch_edit.html
   ➡️ Créer batch_alerts.html
```

---

### 2️⃣ MOUVEMENTS DE STOCK DÉTAILLÉS

#### ✅ CE QUI EXISTE DÉJÀ:

**Table `StockMovement` (models.py:263-277)**:
```python
class StockMovement(db.Model):
    id, product_id, pharmacy_id, movement_type, quantity
    reference, notes, created_by, created_at
```

**Routes Existantes** (`app/routes/stock.py`):
- `/stock/` - Liste mouvements (ligne 12)
- `/stock/export/<format>` - Export (ligne 36)

**Template Existant**:
- `app/templates/stock/index.html` - Liste mouvements

#### ❌ CE QUI MANQUE:

1. **Champs Manquants dans StockMovement**:
   - ❌ `movement_subtype` (sale, transfer_in, transfer_out, adjustment_in, adjustment_out, return, loss, expiry)
   - ❌ `batch_id` (lien avec lot)
   - ❌ `from_pharmacy_id` (pour transferts)
   - ❌ `to_pharmacy_id` (pour transferts)
   - ❌ `unit_cost` (coût unitaire)
   - ❌ `total_value` (valeur totale)
   - ❌ `reference_type` (sale, purchase, transfer, adjustment)
   - ❌ `reference_id` (ID référence)

2. **Fonctionnalités Routes**:
   - ❌ Filtres avancés (type, sous-type, période, utilisateur, produit, pharmacie)
   - ❌ Vue détaillée mouvement (`/stock/movements/<id>`)
   - ❌ Mouvements par produit (`/stock/movements/product/<id>`)
   - ❌ Mouvements par pharmacie (`/stock/movements/pharmacy/<id>`)
   - ❌ Mouvements par utilisateur (`/stock/movements/user/<id>`)
   - ❌ Statistiques mouvements (`/stock/movements/stats`)
   - ❌ Rapport valeur mouvements

3. **Templates Manquants**:
   - ❌ Enrichir `stock/index.html` (filtres avancés, graphiques)
   - ❌ `stock/movement_view.html` - Détails mouvement
   - ❌ `stock/movements_stats.html` - Statistiques

4. **Enregistrements Automatiques**:
   - ❌ Lors ventes POS
   - ❌ Lors transferts
   - ❌ Lors ajustements
   - ❌ Lors retours

#### 📍 OÙ IMPLÉMENTER:

**Fichiers à Modifier**:
```
1. app/models.py (ligne 263-277)
   ➡️ Ajouter champs manquants à StockMovement
   ➡️ Ajouter méthodes helper (get_by_product, get_by_pharmacy)

2. app/routes/stock.py (ligne 12-66)
   ➡️ Enrichir route / avec filtres avancés
   ➡️ Ajouter /movements/<id>
   ➡️ Ajouter /movements/product/<id>
   ➡️ Ajouter /movements/pharmacy/<id>
   ➡️ Ajouter /movements/stats
   ➡️ Améliorer export avec plus de détails

3. app/routes/pos.py, sales.py, stock.py
   ➡️ Enregistrer automatiquement mouvements détaillés

4. app/templates/stock/index.html
   ➡️ Ajouter filtres avancés (datepicker, multi-select)
   ➡️ Ajouter graphiques (Chart.js)
   ➡️ Ajouter indicateurs (total entrées/sorties/valeur)

5. Créer app/templates/stock/
   ➡️ movement_view.html
   ➡️ movements_stats.html
```

---

### 3️⃣ JOURNAL D'ACTIVITÉS (Activity Log)

#### ✅ CE QUI EXISTE DÉJÀ:

**Table `Audit` (models.py:379-390)**:
```python
class Audit(db.Model):
    id, user_id, action, details, ip_address, created_at
```

**Routes Existantes** (`app/routes/audits.py`):
- `/audits/` - Liste audits (ligne 11)
- Filtres: user_id, action, date_from, date_to

**Template Existant**:
- `app/templates/audits/index.html`

#### ❌ CE QUI MANQUE:

1. **Champs Manquants dans Audit**:
   - ❌ `module` (products, sales, users, stock, etc.)
   - ❌ `record_id` (ID enregistrement concerné)
   - ❌ `action_type` (create, update, delete, view, export, login, logout)
   - ❌ `old_value` (valeur avant)
   - ❌ `new_value` (valeur après)
   - ❌ `result` (success, failed, denied)
   - ❌ `user_agent` (navigateur)
   - ❌ `session_id`

2. **Fonctionnalités Routes**:
   - ❌ Filtres par module (`/audits?module=sales`)
   - ❌ Filtres par type action (`/audits?action_type=delete`)
   - ❌ Filtres par résultat (`/audits?result=failed`)
   - ❌ Vue détaillée audit (`/audits/<id>`)
   - ❌ Dashboard activités (`/audits/dashboard`)
   - ❌ Alertes actions suspectes (`/audits/alerts`)
   - ❌ Export détaillé

3. **Helper Universel**:
   - ❌ Créer `app/helpers/activity_logger.py`
   - ❌ Fonction `log_activity(action, module, details)`
   - ❌ Auto-capture IP, user_agent, session

4. **Intégration Partout**:
   - ❌ Dans TOUTES les routes (create, update, delete)
   - ❌ Dans auth (login, logout, failed attempts)
   - ❌ Dans exports
   - ❌ Dans validations
   - ❌ Dans accès refusé (403)

5. **Templates**:
   - ❌ Enrichir `audits/index.html` (filtres, graphiques, stats)
   - ❌ `audits/view.html` - Détails audit
   - ❌ `audits/dashboard.html` - Dashboard activité
   - ❌ `audits/alerts.html` - Activités suspectes

#### 📍 OÙ IMPLÉMENTER:

**Fichiers à Modifier**:
```
1. app/models.py (ligne 379-390)
   ➡️ Ajouter champs manquants à Audit
   ➡️ Renommer en ActivityLog si nécessaire

2. Créer app/helpers/activity_logger.py (NOUVEAU)
   ➡️ Fonction log_activity()
   ➡️ Auto-capture contexte (IP, user, module)
   ➡️ Format JSON pour old_value/new_value

3. app/routes/audits.py
   ➡️ Enrichir route / avec filtres avancés
   ➡️ Ajouter /audits/<id>
   ➡️ Ajouter /audits/dashboard
   ➡️ Ajouter /audits/alerts
   ➡️ Améliorer export

4. TOUTES les routes (products, sales, users, etc.)
   ➡️ Importer activity_logger
   ➡️ Ajouter log_activity() après chaque action
   ➡️ Capturer before/after pour updates

5. app/routes/auth.py
   ➡️ Logger login success/failed
   ➡️ Logger logout
   ➡️ Logger password reset

6. app/templates/audits/
   ➡️ Enrichir index.html (filtres module, type, résultat)
   ➡️ Créer view.html
   ➡️ Créer dashboard.html (graphiques Chart.js)
   ➡️ Créer alerts.html
```

---

### 4️⃣ VENTES TEMPORAIRES (Temp Sales)

#### ✅ CE QUI EXISTE DÉJÀ! (SURPRISE!)

**Table `TempSale` (models.py:665-690)**:
```python
class TempSale(db.Model):
    id, reference, customer_id, created_by, pharmacy_id
    total_amount, discount, items_data, payment_method
    notes, status, validated_by, validated_at, sale_id
    rejection_reason, created_at, updated_at
```

**Logique Existante** (`app/routes/sales.py:309-410`):
- `validate_temp_sale(id)` - Valider vente temporaire
- `reject_temp_sale(id)` - Rejeter vente temporaire

**Logique POS** (`app/routes/pos.py:88-108`):
- Création TempSale lors de vente

#### ❌ CE QUI MANQUE:

1. **Routes Manquantes**:
   - ❌ `/sales/temp` - Liste ventes temporaires
   - ❌ `/sales/temp/<id>` - Voir détails
   - ❌ `/sales/temp/<id>/edit` - Modifier brouillon
   - ❌ `/sales/temp/<id>/resume` - Reprendre vente
   - ❌ `/sales/temp/<id>/delete` - Supprimer brouillon
   - ❌ `/sales/temp/export` - Export

2. **Fonctionnalités POS**:
   - ❌ Bouton "Sauvegarder comme brouillon" dans POS
   - ❌ Bouton "Reprendre brouillon" dans POS
   - ❌ Liste des brouillons en cours
   - ❌ Auto-save toutes les 30 secondes

3. **Templates Manquants**:
   - ❌ `sales/temp_index.html` - Liste brouillons
   - ❌ `sales/temp_view.html` - Détails brouillon
   - ❌ Intégrer dans `pos/index.html` - Section "Brouillons"

4. **Notifications**:
   - ❌ Notifier quand brouillon validé
   - ❌ Notifier quand brouillon rejeté

#### 📍 OÙ IMPLÉMENTER:

**Fichiers à Modifier**:
```
1. app/routes/sales.py
   ➡️ Ajouter route /sales/temp (ligne ~33 utilise déjà TempSale)
   ➡️ Ajouter /sales/temp/<id>
   ➡️ Ajouter /sales/temp/<id>/edit
   ➡️ Ajouter /sales/temp/<id>/resume
   ➡️ Ajouter /sales/temp/<id>/delete
   ➡️ Ajouter /sales/temp/export

2. app/routes/pos.py (ligne 88-108)
   ➡️ Ajouter endpoint /pos/save-draft
   ➡️ Ajouter endpoint /pos/load-draft/<id>
   ➡️ Ajouter endpoint /pos/list-drafts

3. app/templates/pos/index.html
   ➡️ Ajouter bouton "Sauvegarder brouillon"
   ➡️ Ajouter modal liste brouillons
   ➡️ Ajouter auto-save JS

4. Créer app/templates/sales/
   ➡️ temp_index.html
   ➡️ temp_view.html

5. app/templates/includes/sidenav.html
   ➡️ Ajouter lien "Ventes Brouillons" dans menu Ventes
```

---

### 5️⃣ CONTACTS PROFESSIONNELS

#### ✅ CE QUI EXISTE (PARTIELLEMENT):

**Module Suppliers** existe:
- Table `Supplier` (models.py:635-664)
- Routes `app/routes/suppliers.py`
- Templates `app/templates/suppliers/`

#### ❌ CE QUI MANQUE:

Créer nouveau module **Contacts** séparé ou enrichir **Suppliers**?

**Option 1: Enrichir Suppliers** (Plus simple):
1. ❌ Ajouter champs à Supplier:
   - `contact_type` (supplier, partner, service_provider, other)
   - `primary_contact_name`
   - `primary_contact_phone`
   - `primary_contact_email`
   - `secondary_contact_name`
   - `secondary_contact_phone`
   - `website`
   - `tax_id`
   - `notes`

2. ❌ Enrichir routes suppliers avec filtres par type

**Option 2: Nouveau Module Contacts** (Plus complet):
1. ❌ Créer table `Contact` dans models.py
2. ❌ Créer `app/routes/contacts.py`
3. ❌ Créer `app/templates/contacts/`

#### 📍 OÙ IMPLÉMENTER:

**Option Recommandée: Enrichir Suppliers**
```
1. app/models.py (ligne 635-664)
   ➡️ Ajouter champs contact à Supplier

2. app/routes/suppliers.py
   ➡️ Ajouter filtres par type
   ➡️ Améliorer formulaires

3. app/templates/suppliers/
   ➡️ Enrichir create.html et edit.html
   ➡️ Améliorer show.html avec infos contact
```

---

## 📊 PRIORITÉS D'IMPLÉMENTATION

### 🔴 PHASE 1 - CRITIQUE (Semaine 1-2):

#### 1. Gestion par Lots COMPLÈTE
**Durée**: 2-3 jours
**Fichiers**:
- ✏️ Modifier `app/models.py` (ProductBatch + BatchMovement)
- ✏️ Enrichir `app/routes/stock.py` (6 nouvelles routes)
- ✏️ Modifier `app/routes/pos.py` (logique FEFO)
- ✏️ Améliorer templates `stock/batches*.html` (4 fichiers)

#### 2. Mouvements Stock Détaillés
**Durée**: 1-2 jours
**Fichiers**:
- ✏️ Modifier `app/models.py` (StockMovement)
- ✏️ Enrichir `app/routes/stock.py` (4 nouvelles routes)
- ✏️ Améliorer `stock/index.html`
- ✏️ Créer `stock/movements_stats.html`

#### 3. Journal d'Activités Complet
**Durée**: 2 jours
**Fichiers**:
- ✏️ Modifier `app/models.py` (Audit)
- 🆕 Créer `app/helpers/activity_logger.py`
- ✏️ Enrichir `app/routes/audits.py`
- ✏️ Modifier TOUTES routes (ajouter logging)
- ✏️ Améliorer `audits/index.html`
- 🆕 Créer `audits/dashboard.html`

### 🟡 PHASE 2 - IMPORTANT (Semaine 3):

#### 4. Ventes Temporaires Interface
**Durée**: 1 jour
**Fichiers**:
- ✏️ Enrichir `app/routes/sales.py` (5 routes)
- ✏️ Enrichir `app/routes/pos.py` (3 routes)
- ✏️ Modifier `pos/index.html` (boutons + modal)
- 🆕 Créer `sales/temp_index.html`
- 🆕 Créer `sales/temp_view.html`

#### 5. Contacts/Enrichir Suppliers
**Durée**: 1 jour
**Fichiers**:
- ✏️ Enrichir `app/models.py` (Supplier)
- ✏️ Améliorer `app/routes/suppliers.py`
- ✏️ Améliorer templates `suppliers/*.html`

---

## 📝 RÉSUMÉ FICHIERS À MODIFIER

### Fichiers Principaux:
```
✏️ MODIFIER:
1. app/models.py (5 modèles: ProductBatch, StockMovement, Audit, Supplier + 1 nouveau BatchMovement)
2. app/routes/stock.py (10 nouvelles routes)
3. app/routes/audits.py (4 nouvelles routes)
4. app/routes/sales.py (5 routes temp_sales)
5. app/routes/pos.py (logique FEFO + brouillons)
6. app/routes/suppliers.py (enrichir)
7. TOUTES routes/*.py (ajouter activity logging)

🆕 CRÉER:
8. app/helpers/activity_logger.py (NOUVEAU module)

✏️ TEMPLATES MODIFIER:
9. app/templates/stock/batches.html
10. app/templates/stock/index.html
11. app/templates/audits/index.html
12. app/templates/pos/index.html
13. app/templates/suppliers/*.html

🆕 TEMPLATES CRÉER:
14. app/templates/stock/batch_view.html
15. app/templates/stock/batch_edit.html
16. app/templates/stock/batch_alerts.html
17. app/templates/stock/movement_view.html
18. app/templates/stock/movements_stats.html
19. app/templates/audits/view.html
20. app/templates/audits/dashboard.html
21. app/templates/audits/alerts.html
22. app/templates/sales/temp_index.html
23. app/templates/sales/temp_view.html
```

---

## ✅ CONCLUSION

**EXCELLENTE NOUVELLE**: Les structures de base existent déjà!

### Ce qu'on a:
- ✅ ProductBatch (à enrichir)
- ✅ StockMovement (à enrichir)
- ✅ Audit (à enrichir)
- ✅ TempSale (complet! Juste besoin UI)
- ✅ Supplier (à enrichir pour contacts)

### Ce qu'il faut:
- 📝 Enrichir 5 modèles existants
- 📝 Ajouter ~25 routes dans fichiers existants
- 🆕 Créer 1 helper (activity_logger)
- 📝 Améliorer 6 templates existants
- 🆕 Créer 10 nouveaux templates

**Durée Totale Estimée**: 5-7 jours de développement

---

**Voulez-vous commencer par la Gestion par Lots (la plus critique)?**

© 2025 Marco Pharma | Plan d'Implémentation Modules Existants


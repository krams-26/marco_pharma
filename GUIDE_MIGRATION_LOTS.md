# Guide de Migration - Gestion Complète des Lots

## 📋 RÉSUMÉ

Cette migration ajoute la gestion complète des lots pharmaceutiques à Marco-Pharma, incluant:
- ✅ Traçabilité complète par lot
- ✅ Gestion FEFO (First Expired First Out)
- ✅ Alertes d'expiration
- ✅ Historique des mouvements par lot
- ✅ Multi-pharmacies par lot

---

## 🚨 IMPORTANT - AVANT DE COMMENCER

### 1. **SAUVEGARDER LA BASE DE DONNÉES**

```bash
# Windows (PowerShell)
cd C:\wamp64\bin\mysql\mysql8.0.x\bin\
.\mysqldump.exe -u root -p marco_pharma > C:\backup_avant_migration_lots.sql

# Linux/Mac
mysqldump -u root -p marco_pharma > ~/backup_avant_migration_lots.sql
```

### 2. **VÉRIFIER LES PRÉREQUIS**

- ✅ Application arrêtée
- ✅ Sauvegarde effectuée
- ✅ Accès administrateur à MySQL
- ✅ Environnement de test disponible (recommandé)

---

## 📦 CE QUI VA ÊTRE MODIFIÉ

### Tables Modifiées:
1. **`product_batches`** - 8 nouveaux champs ajoutés
2. **`batch_movements`** - Nouvelle table créée

### Nouveaux Champs `product_batches`:
```sql
pharmacy_id INT             -- Pharmacie du lot
initial_quantity INT        -- Quantité initiale
unit_cost DECIMAL(10,2)     -- Coût unitaire
manufacture_date DATE       -- Date de fabrication
supplier_id INT             -- ID fournisseur
status VARCHAR(20)          -- active, expired, depleted, recalled
created_at TIMESTAMP        -- Date création
updated_at TIMESTAMP        -- Date modification
```

### Nouvelle Table `batch_movements`:
```sql
id INT                      -- Clé primaire
batch_id INT                -- Référence au lot
movement_type VARCHAR(20)   -- Type: entry, sale, transfer, etc.
quantity INT                -- Quantité du mouvement
reference_type VARCHAR(50)  -- Type de référence
reference_id INT            -- ID référence
user_id INT                 -- Utilisateur
notes TEXT                  -- Notes
created_at TIMESTAMP        -- Date/heure
```

---

## 🔧 ÉTAPES D'INSTALLATION

### Étape 1: Exécuter la Migration SQL

```bash
# Se connecter à MySQL
mysql -u root -p marco_pharma

# Dans MySQL, exécuter:
source C:/Users/MARCO PHARMA/Downloads/Marco-Pharma/migrations/upgrade_batch_management.sql

# Ou directement depuis PowerShell:
Get-Content migrations/upgrade_batch_management.sql | mysql -u root -p marco_pharma
```

### Étape 2: Vérifier la Migration

```sql
-- Vérifier les nouveaux champs
DESC product_batches;

-- Vérifier la nouvelle table
DESC batch_movements;

-- Vérifier les données
SELECT COUNT(*) AS total_lots FROM product_batches;
SELECT COUNT(*) AS total_movements FROM batch_movements;
SELECT status, COUNT(*) AS count FROM product_batches GROUP BY status;
```

### Étape 3: Vérifier l'ID Administrateur

```sql
-- Trouver l'ID de l'administrateur
SELECT id, username, role FROM users WHERE role = 'admin' LIMIT 1;

-- Si l'ID n'est pas 1, mettre à jour le script ligne 89:
-- Remplacer: 1 AS user_id
-- Par: [ID_ADMIN] AS user_id
```

### Étape 4: Redémarrer l'Application

```bash
# Dans Marco-Pharma directory
python run.py
# ou
python main.py
```

---

## ✅ TESTS POST-MIGRATION

### 1. Tester l'Affichage des Lots

Aller sur: `http://localhost:5000/stock/batches`

**Vérifier**:
- ✅ Les lots s'affichent correctement
- ✅ Les statuts sont visibles (Actif, Expiré, etc.)
- ✅ Les filtres fonctionnent
- ✅ Les statistiques s'affichent

### 2. Tester une Vue Détaillée

Cliquer sur un lot → Actions → Voir détails

**Vérifier**:
- ✅ Toutes les informations s'affichent
- ✅ L'historique des mouvements est visible
- ✅ Le statut est correct

### 3. Tester l'Ajout d'un Lot

Aller sur: `http://localhost:5000/stock/add-batch`

**Vérifier**:
- ✅ Le formulaire s'affiche
- ✅ Tous les champs sont présents
- ✅ La création fonctionne
- ✅ Un mouvement est créé automatiquement

### 4. Tester les Alertes

Aller sur: `http://localhost:5000/stock/batches/expiring`

**Vérifier**:
- ✅ Les lots expirant s'affichent
- ✅ Les statistiques sont correctes
- ✅ Les priorités sont bien affichées

### 5. Tester l'Export

Cliquer sur: Exporter → Excel ou CSV

**Vérifier**:
- ✅ Le fichier se télécharge
- ✅ Toutes les colonnes sont présentes
- ✅ Les données sont correctes

---

## 🐛 DÉPANNAGE

### Erreur: "Table doesn't exist"

```sql
-- Vérifier que les tables existent
SHOW TABLES LIKE '%batch%';

-- Si batch_movements n'existe pas, relancer la migration
```

### Erreur: "Foreign key constraint fails"

```sql
-- Vérifier les relations
SELECT 
    pb.id,
    pb.product_id,
    p.id AS product_exists
FROM product_batches pb
LEFT JOIN products p ON pb.product_id = p.id
WHERE p.id IS NULL;

-- Supprimer les lots orphelins si nécessaire
DELETE FROM product_batches WHERE product_id NOT IN (SELECT id FROM products);
```

### Erreur: "Column already exists"

```sql
-- La migration a déjà été exécutée partiellement
-- Vérifier l'état actuel:
DESC product_batches;

-- Si nécessaire, rollback puis relancer
```

### Les Lots ne s'Affichent Pas

1. **Vérifier les erreurs Python:**
   ```bash
   # Regarder les logs de l'application
   ```

2. **Vérifier les imports:**
   ```python
   # Dans routes/stock.py, vérifier:
   from app.models import BatchMovement
   ```

3. **Vérifier les permissions:**
   ```sql
   -- Vérifier que l'utilisateur a la permission 'manage_stock'
   SELECT username, permissions FROM users;
   ```

---

## 🔄 ROLLBACK (Annulation)

Si vous devez annuler la migration:

```sql
-- ATTENTION: Ceci supprimera toutes les données de gestion des lots!

-- 1. Sauvegarder d'abord batch_movements si nécessaire
CREATE TABLE batch_movements_backup AS SELECT * FROM batch_movements;

-- 2. Supprimer la table
DROP TABLE IF EXISTS batch_movements;

-- 3. Supprimer les colonnes ajoutées
ALTER TABLE product_batches 
DROP COLUMN pharmacy_id,
DROP COLUMN initial_quantity,
DROP COLUMN unit_cost,
DROP COLUMN manufacture_date,
DROP COLUMN supplier_id,
DROP COLUMN status,
DROP COLUMN created_at,
DROP COLUMN updated_at;

-- 4. Supprimer les index
DROP INDEX IF EXISTS idx_batch_number ON product_batches;
DROP INDEX IF EXISTS idx_expiry_date ON product_batches;
DROP INDEX IF EXISTS idx_status ON product_batches;
DROP INDEX IF EXISTS idx_pharmacy_id ON product_batches;

-- 5. Restaurer depuis la sauvegarde
-- mysql -u root -p marco_pharma < backup_avant_migration_lots.sql
```

---

## 📊 STATISTIQUES ATTENDUES

Après la migration, vous devriez voir:

```
✅ Lots Totaux: X lots
✅ Lots Actifs: ~80-90% des lots
✅ Lots Expirant: ~5-10% des lots
✅ Lots Expirés: ~0-5% des lots
✅ Mouvements Créés: 1 mouvement par lot (entrée initiale)
```

---

## 🎯 PROCHAINES ÉTAPES

Après cette migration réussie, vous pouvez:

1. ✅ **Utiliser la gestion par lots** - Ajouter des lots avec toutes les informations
2. ✅ **Configurer les alertes** - Surveiller les expirations
3. ✅ **Exporter les données** - Rapports Excel/CSV complets
4. ⏭️ **Intégrer FEFO dans POS** - Sélection automatique du lot le plus proche expiration
5. ⏭️ **Enregistrer mouvements détaillés** - Traçabilité complète
6. ⏭️ **Ajouter journal d'activités** - Audit complet

---

## 📞 SUPPORT

En cas de problème:

1. **Vérifier les logs** de l'application
2. **Vérifier les erreurs SQL** dans MySQL
3. **Consulter** `PLAN_IMPLEMENTATION_MODULES_EXISTANTS.md`
4. **Restaurer** depuis la sauvegarde si nécessaire

---

## ✨ NOUVELLES FONCTIONNALITÉS DISPONIBLES

### Routes Disponibles:

```
GET  /stock/batches                    - Liste des lots avec filtres
GET  /stock/batches/<id>              - Détails d'un lot
GET  /stock/batches/<id>/edit         - Modifier un lot
GET  /stock/batches/<id>/movements    - Historique mouvements
GET  /stock/batches/expiring          - Alertes expiration
GET  /stock/batches/export/<format>   - Export Excel/CSV
POST /stock/add-batch                 - Ajouter un lot
```

### Templates Disponibles:

```
stock/batches.html         - Liste enrichie avec stats et filtres
stock/batch_view.html      - Vue détaillée complète
stock/batch_edit.html      - Formulaire édition
stock/batch_movements.html - Historique mouvements
stock/batch_alerts.html    - Alertes expiration
```

---

**🎉 Migration Terminée avec Succès!**

Vous disposez maintenant d'un système complet de gestion des lots pharmaceutiques conforme aux normes de traçabilité!

---

© 2025 Marco Pharma | Guide de Migration Lots


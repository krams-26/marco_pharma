# Pages utilisant Bootstrap 5 au lieu d'Argon/Bootstrap 4

## 📊 ANALYSE

### ⚠️ CLASSES BOOTSTRAP 5 DÉTECTÉES

Argon Dashboard utilise **Bootstrap 4**, mais certaines pages utilisent des classes **Bootstrap 5**:

#### Classes BS5 Incompatibles:
- `form-select` → Devrait être `form-control` (Argon/BS4)
- `form-check` → Devrait être `custom-control` (Argon/BS4)
- `btn-close` → Devrait être `close` (Argon/BS4)
- `g-3`, `gap-*` → Spacing BS5

---

## 📋 PAGES AVEC BOOTSTRAP 5 (25 fichiers)

### FORMULAIRES PRODUITS:
1. ❌ `products/add.html` - form-select
2. ❌ `products/edit.html` - form-select

### FORMULAIRES CLIENTS:
3. ❌ `customers/add.html` - form-select
4. ❌ `customers/edit.html` - form-select

### FORMULAIRES UTILISATEURS:
5. ❌ `users/add.html` - form-select
6. ❌ `users/edit.html` - form-select

### FORMULAIRES PHARMACIES:
7. ❌ `pharmacies/create.html` - form-select
8. ❌ `pharmacies/edit.html` - form-select
9. ❌ `pharmacies/assign_user.html` - form-select

### FORMULAIRES STOCK:
10. ❌ `stock/add_batch.html` - form-select
11. ❌ `stock/adjust.html` - form-select
12. ❌ `stock/transfer.html` - form-select

### FORMULAIRES RH:
13. ❌ `hr/add_absence.html` - form-select
14. ❌ `hr/add_leave_request.html` - form-select
15. ❌ `hr/add_credit_request.html` - form-select

### FORMULAIRES PROFORMA:
16. ❌ `proforma/create.html` - form-select
17. ❌ `proforma/edit.html` - form-select

### AUTRES FORMULAIRES:
18. ❌ `credit_sales/show.html` - form-select
19. ❌ `cashier/add_transaction.html` - form-select
20. ❌ `tasks/*` - 3 fichiers
21. ❌ `suppliers/*` - 2 fichiers
22. ❌ `evaluation/*` - 2 fichiers

### PAGE COMPLEXE:
23. ❌ `pos/index.html` - Utilise BS5 + beaucoup de JS custom

---

## 🔄 CONVERSIONS NÉCESSAIRES

### Bootstrap 5 → Argon (Bootstrap 4)

| Bootstrap 5 | Argon (Bootstrap 4) |
|-------------|---------------------|
| `form-select` | `form-control` |
| `form-check` | `custom-control custom-checkbox` |
| `form-check-input` | `custom-control-input` |
| `form-check-label` | `custom-control-label` |
| `btn-close` | `close` |
| `mb-3` | `mb-3` (OK) |
| `g-3` | Utiliser `row` avec margins |
| `gap-2` | Utiliser margins individuelles |

---

## 🎯 RECOMMANDATION

### Option A: Tout Convertir en Argon/BS4 ⭐
- Uniformité totale
- Cohérence design
- Temps: ~30-40 min

### Option B: Garder BS5 pour Formulaires
- Formulaires fonctionnent déjà
- Pas d'impact visuel majeur
- Rapide mais incohérent

### Option C: Hybride
- Listes/Dashboards: Argon ✅
- Formulaires: BS5 acceptable
- Ajouter juste le header Argon

---

## 💡 MA RECOMMANDATION

**Option C - Hybride** car:
1. Les pages principales (listes) sont déjà Argon ✅
2. Les formulaires fonctionnent bien
3. L'impact visuel est minimal
4. On gagne du temps

Mais si vous voulez la **cohérence totale**, je peux convertir toutes les `form-select` en `form-control` Argon.

Voulez-vous que je:
1. **Convertisse tout en Argon/BS4** (cohérence totale)
2. **Laisse les formulaires en BS5** (gain de temps)
3. **Ajoute juste les headers Argon** aux formulaires

---

© 2025 Marco Pharma | Analyse Bootstrap


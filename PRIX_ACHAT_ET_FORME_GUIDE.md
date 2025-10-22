# Guide - Prix d'Achat et Forme Pharmaceutique

## ✅ MODIFICATIONS EFFECTUÉES

### 1. Prix d'Achat Ajouté dans les Listes

#### Produits (`products/index.html`)
**Colonnes de la table**:
1. Produit
2. Code-barres
3. **Forme** (au lieu de Catégorie)
4. **Prix d'Achat** ⭐ NOUVEAU
   - Affiché en USD
   - Conversion CDF en petit
   - Couleur primaire (bleu)
5. Prix de Vente
   - Affiché en USD
   - Conversion CDF en petit
   - Couleur success (vert)
6. Stock
7. Pharmacie (admin uniquement)
8. Actions

**Affichage du Prix d'Achat**:
```html
<td>
  <span class="text-primary font-weight-bold">${{ "%.2f"|format(product.purchase_price) }}</span><br>
  <small class="text-muted">{{ (product.purchase_price|usd_to_cdf)|format_number }} FC</small>
</td>
```

### 2. Catégorie → Forme

**26 remplacements dans 11 fichiers**:

| Fichier | Remplacements |
|---------|---------------|
| `products/add.html` | 3 |
| `products/edit.html` | 3 |
| `products/import.html` | 3 |
| `products/index.html` | 1 |
| `products/alerts.html` | 2 |
| `reports/products.html` | 2 |
| `reports/stock.html` | 4 |
| `reports/expenses.html` | 2 |
| `suppliers/show.html` | 2 |
| `base.html` | 2 |
| `auth/login.html` | 2 |

**Changements**:
- "Catégorie" → "Forme"
- "catégorie" → "forme"
- "Catégories" → "Formes"
- Labels et placeholders mis à jour
- Champ DB reste "category" (compatibilité)

---

## 📋 OÙ AJOUTER LE PRIX D'ACHAT

### Pages de Liste (avec colonnes):

#### ✅ **Produits** - FAIT
- Prix Achat avant Prix Vente
- Dual display (USD + FC)

#### ⏳ **Ventes (Détails)**
À ajouter dans `sales/view.html`:
```html
<th>Produit</th>
<th>Prix Achat</th>  <!-- NOUVEAU -->
<th>Prix Vente</th>
<th>Quantité</th>
<th>Sous-total</th>
<th>Marge</th>       <!-- NOUVEAU: Vente - Achat -->
```

#### ⏳ **POS (Point de Vente)**
À ajouter dans `pos/index.html`:
- Afficher prix achat dans la sélection de produit
- Calculer marge en temps réel
- Afficher marge totale du panier

#### ⏳ **Proforma**
À ajouter dans `proforma/show.html` et `proforma/print.html`:
- Prix achat par ligne
- Marge par ligne
- Marge totale

#### ⏳ **Stock (Lots)**
À ajouter dans `stock/batches.html`:
- Prix achat du lot
- Prix achat moyen
- Valeur totale du stock

---

## 💰 CALCUL DE MARGE

### Formule:
```
Marge Unitaire = Prix Vente - Prix Achat
Marge % = ((Prix Vente - Prix Achat) / Prix Achat) × 100
```

### Exemple de Template:

```html
<!-- Marge en valeur -->
<td>
  <span class="badge badge-success">
    ${{ "%.2f"|format(item.unit_price - product.purchase_price) }}
  </span>
</td>

<!-- Marge en % -->
<td>
  {% set margin_pct = ((item.unit_price - product.purchase_price) / product.purchase_price * 100) %}
  <span class="badge {% if margin_pct > 30 %}badge-success{% elif margin_pct > 15 %}badge-warning{% else %}badge-danger{% endif %}">
    {{ "%.1f"|format(margin_pct) }}%
  </span>
</td>
```

### Indicateurs de Marge:
- **> 30%**: Badge vert (Excellente marge)
- **15-30%**: Badge orange (Bonne marge)
- **< 15%**: Badge rouge (Marge faible)

---

## 🎯 PERMISSIONS POUR PRIX D'ACHAT

### Affichage Restreint:

```html
{% if current_user.role in ['admin', 'gestionnaire', 'pharmacien'] %}
<th>Prix d'Achat</th>
<th>Marge</th>
{% endif %}
```

### Rôles avec Accès:
- ✅ **Admin**: Accès complet
- ✅ **Gestionnaire**: Accès complet
- ✅ **Pharmacien**: Accès complet
- ❌ **Vendeur**: Pas d'accès (voit uniquement prix vente)

---

## 📊 RAPPORTS À CRÉER

### 1. Rapport de Marges
- Marge par produit
- Marge par catégorie/forme
- Marge par pharmacie
- Marge globale

### 2. Rapport de Rentabilité
- Produits les plus rentables
- Produits à faible marge
- Évolution des marges

### 3. Analyse Coût/Vente
- Coût total d'achat
- Revenu total de vente
- Bénéfice net
- ROI (Return on Investment)

---

## 🔧 IMPLÉMENTATION RAPIDE

### Pour Ajouter Prix d'Achat dans une Liste:

```html
<!-- Dans thead -->
<th>Prix d'Achat</th>
<th>Prix de Vente</th>

<!-- Dans tbody -->
<td>
  <span class="text-primary font-weight-bold">${{ "%.2f"|format(item.purchase_price) }}</span><br>
  <small class="text-muted">{{ (item.purchase_price|usd_to_cdf)|format_number }} FC</small>
</td>
<td>
  <span class="text-success font-weight-bold">${{ "%.2f"|format(item.selling_price) }}</span><br>
  <small class="text-muted">{{ (item.selling_price|usd_to_cdf)|format_number }} FC</small>
</td>
```

### Pour Ajouter la Marge:

```html
<th>Marge</th>

<!-- Dans tbody -->
<td>
  {% set margin = item.selling_price - item.purchase_price %}
  {% set margin_pct = (margin / item.purchase_price * 100) if item.purchase_price > 0 else 0 %}
  
  <span class="font-weight-bold">${{ "%.2f"|format(margin) }}</span><br>
  <span class="badge {% if margin_pct > 30 %}badge-success{% elif margin_pct > 15 %}badge-warning{% else %}badge-danger{% endif %}">
    {{ "%.1f"|format(margin_pct) }}%
  </span>
</td>
```

---

## 📁 FICHIERS À MODIFIER

### Templates à Adapter:

1. **POS (Prioritaire)**
   - `pos/index.html` - Afficher prix achat dans recherche produit
   - Calculer marge en temps réel

2. **Ventes Détails**
   - `sales/view.html` - Ajouter colonnes prix achat et marge
   - Calculer marge totale de la vente

3. **Proforma**
   - `proforma/show.html` - Prix achat par ligne
   - `proforma/print.html` - Option marge

4. **Stock (Lots)**
   - `stock/batches.html` - Prix achat du lot
   - Valeur totale du stock

5. **Rapports**
   - `reports/products.html` - Rapport de marges
   - `reports/sales.html` - Analyse rentabilité

### Routes à Modifier:

Ajouter prix d'achat dans les exports:

```python
headers = ['Nom', 'Prix Achat', 'Prix Vente', 'Marge', 'Marge %', ...]

data.append({
    'Prix Achat': p.purchase_price,
    'Prix Vente': p.selling_price,
    'Marge': p.selling_price - p.purchase_price,
    'Marge %': ((p.selling_price - p.purchase_price) / p.purchase_price * 100) if p.purchase_price > 0 else 0
})
```

---

## ✨ RÉSULTAT ACTUEL

### Produits - Liste:

```
┌────────────┬────────────┬───────┬────────────┬────────────┬───────┐
│ Produit    │ Code-barre │ Forme │ Prix Achat │ Prix Vente │ Stock │
├────────────┼────────────┼───────┼────────────┼────────────┼───────┤
│ Paracétam. │ 123456     │ Comp. │ $2.50      │ $5.00      │ 100   │
│            │            │       │ 7,000 FC   │ 14,000 FC  │       │
└────────────┴────────────┴───────┴────────────┴────────────┴───────┘
```

---

## 🎯 PROCHAINES ÉTAPES

1. ⏳ **POS** - Ajouter prix achat + marge
2. ⏳ **Ventes Détails** - Ajouter prix achat + marge
3. ⏳ **Proforma** - Ajouter prix achat + marge
4. ⏳ **Stock Lots** - Ajouter prix achat
5. ⏳ **Rapports** - Créer rapport de marges

---

© 2025 Marco Pharma | Prix d'Achat et Forme Implémentés


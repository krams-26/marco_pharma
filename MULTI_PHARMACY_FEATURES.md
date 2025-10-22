# Fonctionnalités Multi-Pharmacies et Import/Export

## 🎯 Objectif

Implémentation complète d'un système multi-pharmacies avec:
1. **Filtrage par pharmacie** (admin uniquement)
2. **Restrictions d'accès** par pharmacie pour les utilisateurs non-admin
3. **Export de données** en CSV et Excel
4. **Import de données** depuis CSV

---

## ✅ Fonctionnalités Implémentées

### 1. **Système de Permissions Multi-Pharmacies**

#### Fichier: `app/pharmacy_utils.py`

Fonctions utilitaires créées:

- `get_accessible_pharmacies()` - Retourne les pharmacies accessibles
  - **Admin**: Toutes les pharmacies
  - **Autres**: Uniquement leurs pharmacies assignées

- `get_accessible_pharmacy_ids()` - Retourne les IDs des pharmacies accessibles

- `filter_by_pharmacy(query, model, pharmacy_filter)` - Filtre SQLAlchemy selon les permissions
  - **Admin**: Peut filtrer par pharmacie spécifique ou voir toutes
  - **Autres**: Ne voient que leurs pharmacies

- `can_access_pharmacy(pharmacy_id)` - Vérifie l'accès à une pharmacie

- `get_current_pharmacy()` - Retourne la pharmacie courante
  - **Admin**: None (accès total)
  - **Autres**: Pharmacie principale

- `is_admin()` - Vérifie si l'utilisateur est admin

#### Exemple d'utilisation:

```python
from app.pharmacy_utils import filter_by_pharmacy, get_accessible_pharmacies, is_admin

# Dans une route
pharmacy_filter = request.args.get('pharmacy_id', 'all')
query = Product.query.filter_by(is_active=True)

# Appliquer le filtre selon les permissions
query = filter_by_pharmacy(query, Product, pharmacy_filter)

# Récupérer les pharmacies pour le menu déroulant (admin uniquement)
pharmacies = get_accessible_pharmacies() if is_admin() else []
```

---

### 2. **Système d'Export/Import**

#### Fichier: `app/export_utils.py`

Fonctions créées:

- `export_to_csv(data, filename, headers)` - Exporte en CSV
- `export_to_excel(data, filename, headers, sheet_name)` - Exporte en Excel avec mise en forme
- `parse_csv_file(file)` - Parse un fichier CSV uploadé
- `validate_import_data(data, required_fields)` - Valide les données d'import

#### Caractéristiques de l'Export Excel:
- En-têtes avec fond bleu (couleur Argon)
- Police blanche en gras pour les en-têtes
- Colonnes auto-ajustées
- Nom de fichier avec timestamp

---

### 3. **Produits avec Filtres et Export/Import**

#### Routes ajoutées dans `app/routes/products.py`:

1. **`GET /products/`** - Liste avec filtre pharmacie
   - Paramètre: `pharmacy_id` (admin uniquement)
   - Filtre automatique selon les permissions

2. **`GET /products/export/<format>`** - Export CSV/Excel
   - Formats: `csv` ou `excel`
   - Respect des filtres actifs (pharmacie, recherche)
   - Colonnes: ID, Nom, Code-barres, Catégorie, Prix, Stock, Pharmacie

3. **`GET|POST /products/import`** - Import depuis CSV
   - Upload de fichier CSV
   - Validation des données
   - Template CSV téléchargeable
   - Rapport d'erreurs détaillé

#### Champs CSV pour Import:
**Obligatoires**:
- Nom
- Prix Vente

**Optionnels**:
- Description, Code-barres, Catégorie, Unité
- Prix Achat, Prix Gros
- Stock, Stock Min
- Fabricant, Fournisseur

---

### 4. **Templates Argon Dashboard**

#### `app/templates/products/index.html`

Nouvelle interface avec design Argon:

- **Header avec Background Gradient**
  - Breadcrumb navigation
  - Boutons "Importer" et "Nouveau"

- **Filtres Contextuels**
  - Filtre pharmacie (admin uniquement)
  - Barre de recherche
  - Application automatique des filtres

- **Boutons d'Export**
  - Menu déroulant avec CSV et Excel
  - Respect des filtres actifs

- **Table Responsive Argon**
  - Design élégant avec badges
  - Colonne "Pharmacie" visible pour admin uniquement
  - Prix en USD + CDF
  - Indicateurs de stock (vert/orange)

- **Pagination Argon**
  - Design cohérent avec le reste
  - Conservation des paramètres de filtre

#### `app/templates/products/import.html`

Page d'import complète:

- **Instructions détaillées**
  - Format CSV expliqué
  - Liste des colonnes
  - Avertissements importants

- **Formulaire d'Upload**
  - Input file stylé Argon
  - Validation côté client
  - Retour visuel

- **Template CSV Téléchargeable**
  - Bouton pour télécharger un exemple
  - Données de démonstration incluses

---

## 🎨 Composants UI Réutilisables

### `app/templates/includes/pharmacy_filter.html`

Filtre pharmacie réutilisable:
- S'affiche uniquement pour les admins
- Liste déroulante avec toutes les pharmacies
- Option "Toutes les Pharmacies"
- Application automatique du filtre
- JavaScript pour soumission automatique

### `app/templates/includes/export_buttons.html`

Boutons d'export réutilisables:
- Menu déroulant Bootstrap
- Options CSV et Excel
- Conservation des paramètres de filtre
- Icônes Font Awesome

---

## 📋 Utilisation

### Pour l'Admin

#### Filtrer par Pharmacie:
1. Aller sur la liste des produits
2. Sélectionner une pharmacie dans le menu déroulant
3. La liste est automatiquement filtrée

#### Exporter des Données:
1. Appliquer les filtres désirés (pharmacie, recherche)
2. Cliquer sur "Exporter"
3. Choisir CSV ou Excel
4. Le fichier est téléchargé avec timestamp

#### Importer des Produits:
1. Cliquer sur "Importer"
2. Télécharger le template CSV (optionnel)
3. Préparer votre fichier CSV
4. Uploader le fichier
5. Les produits sont importés dans votre pharmacie

### Pour les Utilisateurs Non-Admin

- **Filtrage**: Automatique, voient uniquement leurs pharmacies
- **Export**: Disponible, mais uniquement pour leurs données
- **Import**: Disponible, produits ajoutés à leur pharmacie

---

## 🔒 Sécurité et Permissions

### Contrôle d'Accès:
```python
# Tous les utilisateurs voient uniquement leurs données
query = filter_by_pharmacy(query, Product, pharmacy_filter)

# Admin peut choisir 'all' ou une pharmacie spécifique
# Non-admin: filtre automatique sur leurs pharmacies assignées
```

### Validation:
- Vérification des permissions à chaque requête
- Filtrage au niveau de la base de données
- Audit trail pour les imports

---

## 📦 Dépendances

Ajoutée dans `requirements.txt`:
```
openpyxl==3.1.2
```

Installation:
```bash
pip install openpyxl==3.1.2
```

---

## 🚀 Extension à D'autres Modules

Pour ajouter les filtres et exports à d'autres pages:

### 1. Modifier la Route

```python
from app.pharmacy_utils import filter_by_pharmacy, get_accessible_pharmacies, is_admin
from app.export_utils import export_to_csv, export_to_excel

@bp.route('/')
def index():
    pharmacy_filter = request.args.get('pharmacy_id', 'all')
    
    query = Model.query
    query = filter_by_pharmacy(query, Model, pharmacy_filter)
    
    items = query.paginate(page=page, per_page=6)
    pharmacies = get_accessible_pharmacies() if is_admin() else []
    
    return render_template('template.html', 
                         items=items, 
                         pharmacies=pharmacies,
                         pharmacy_filter=pharmacy_filter)
```

### 2. Ajouter Route d'Export

```python
@bp.route('/export/<format>')
def export(format):
    pharmacy_filter = request.args.get('pharmacy_id', 'all')
    
    query = Model.query
    query = filter_by_pharmacy(query, Model, pharmacy_filter)
    items = query.all()
    
    headers = ['Colonne1', 'Colonne2', ...]
    data = [{'Colonne1': item.col1, ...} for item in items]
    
    if format == 'csv':
        return export_to_csv(data, 'nom_fichier', headers)
    else:
        return export_to_excel(data, 'nom_fichier', headers)
```

### 3. Adapter le Template

```html
<!-- Inclure le filtre pharmacie -->
<form method="GET">
    {% if current_user.role == 'admin' and pharmacies %}
    <select name="pharmacy_id" onchange="this.form.submit()">
        <option value="all">Toutes les Pharmacies</option>
        {% for pharmacy in pharmacies %}
        <option value="{{ pharmacy.id }}">{{ pharmacy.name }}</option>
        {% endfor %}
    </select>
    {% endif %}
</form>

<!-- Boutons d'export -->
<div class="btn-group">
    <button data-toggle="dropdown">Exporter</button>
    <div class="dropdown-menu">
        <a href="{{ url_for('bp.export', format='csv') }}?pharmacy_id={{ pharmacy_filter }}">CSV</a>
        <a href="{{ url_for('bp.export', format='excel') }}?pharmacy_id={{ pharmacy_filter }}">Excel</a>
    </div>
</div>
```

---

## 📊 Modules à Étendre

Appliquer les mêmes fonctionnalités à:

- ✅ **Produits** (Fait)
- ⏳ **Ventes** (À faire)
- ⏳ **Clients** (À faire)
- ⏳ **Stock** (À faire)
- ⏳ **Rapports** (À faire)
- ⏳ **Paiements** (À faire)
- ⏳ **RH** (À faire)

---

## 🎯 Avantages

### Pour l'Admin:
- ✅ Vue consolidée de toutes les pharmacies
- ✅ Filtrage facile par pharmacie
- ✅ Export de données pour analyse
- ✅ Import en masse pour gagner du temps

### Pour les Utilisateurs:
- ✅ Accès restreint et sécurisé
- ✅ Vue uniquement de leurs données
- ✅ Export de leurs données
- ✅ Import dans leur pharmacie

### Pour le Système:
- ✅ Sécurité renforcée
- ✅ Audit trail complet
- ✅ Performance optimisée (filtrage DB)
- ✅ Scalabilité

---

## 🐛 Débogage

### Vérifier les Permissions:
```python
from app.pharmacy_utils import get_accessible_pharmacy_ids

# Dans la console Python/Flask shell
ids = get_accessible_pharmacy_ids()
print(f"Pharmacies accessibles: {ids}")
```

### Tester le Filtre:
```python
# Tester avec différents rôles
from app.models import User
admin = User.query.filter_by(role='admin').first()
vendeur = User.query.filter_by(role='vendeur').first()

# Simuler login et tester get_accessible_pharmacies()
```

---

## 📝 Notes Techniques

### Performance:
- Filtrage au niveau SQL (pas en Python)
- Index sur `pharmacy_id` recommandé
- Pagination maintenue (6 items)

### Export:
- Limite mémoire: ~10K lignes recommandé
- Pour plus: implémenter export async/streaming

### Import:
- Validation stricte des données
- Rollback en cas d'erreur
- Rapport détaillé des erreurs

---

## 🎉 Résultat

Système complet multi-pharmacies avec:
- ✅ Filtrage intelligent selon les rôles
- ✅ Export CSV/Excel professionnel
- ✅ Import CSV avec validation
- ✅ Interface Argon Dashboard élégante
- ✅ Sécurité et permissions robustes
- ✅ Réutilisable pour tous les modules

---

© 2025 Marco Pharma | Design Argon Dashboard


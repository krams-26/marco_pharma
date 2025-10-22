from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from app.decorators import require_permission
from flask_login import login_required, current_user
from app.models import db, Product, ProductBatch, Audit, Pharmacy
from app.pharmacy_utils import filter_by_pharmacy, get_accessible_pharmacies, is_admin
from app.export_utils import export_to_csv, export_to_excel, parse_csv_file, validate_import_data
from datetime import datetime

products_bp = Blueprint('products', __name__, url_prefix='/products')

@products_bp.route('/quick-view/<int:id>')
@login_required
def quick_view(id):
    """Vue rapide d'un produit en modal"""
    product = Product.query.get_or_404(id)
    return jsonify({
        'id': product.id,
        'name': product.name,
        'barcode': product.barcode,
        'category': product.category,
        'description': product.description,
        'purchase_price': product.purchase_price,
        'selling_price': product.selling_price,
        'wholesale_price': product.wholesale_price,
        'stock_quantity': product.stock_quantity,
        'min_stock_level': product.min_stock_level,
        'is_low_stock': product.is_low_stock,
        'expiry_date': product.expiry_date.strftime('%d/%m/%Y') if product.expiry_date else None,
        'is_expired': product.is_expired,
        'manufacturer': product.manufacturer,
        'supplier': product.supplier,
        'unit': product.unit,
        'pharmacy_name': product.pharmacy.name if product.pharmacy else 'N/A'
    })

@products_bp.route('/')
@require_permission('manage_products')
def index():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    pharmacy_filter = request.args.get('pharmacy_id', 'all')
    
    query = Product.query.filter_by(is_active=True)
    
    # Filtrage par pharmacie selon les permissions
    query = filter_by_pharmacy(query, Product, pharmacy_filter)
    
    if search:
        query = query.filter(
            db.or_(
                Product.name.ilike(f'%{search}%'),
                Product.barcode.ilike(f'%{search}%'),
                Product.category.ilike(f'%{search}%')
            )
        )
    
    products = query.order_by(Product.created_at.desc()).paginate(
        page=page, per_page=6, error_out=False
    )
    
    # Récupérer les pharmacies accessibles pour le filtre
    pharmacies = get_accessible_pharmacies()
    
    return render_template('products/index.html', 
                         products=products, 
                         search=search,
                         pharmacies=pharmacies,
                         pharmacy_filter=pharmacy_filter)

@products_bp.route('/add', methods=['GET', 'POST'])
@require_permission('manage_products')
def add():
    if request.method == 'POST':
        try:
            primary_pharmacy = current_user.get_primary_pharmacy()
            
            product = Product(
                name=request.form.get('name'),
                description=request.form.get('description'),
                barcode=request.form.get('barcode'),
                category=request.form.get('category'),
                unit=request.form.get('unit', 'piece'),
                purchase_price=float(request.form.get('purchase_price', 0)),
                selling_price=float(request.form.get('selling_price', 0)),
                wholesale_price=float(request.form.get('wholesale_price', 0)),
                stock_quantity=int(request.form.get('stock_quantity', 0)),
                min_stock_level=int(request.form.get('min_stock_level', 10)),
                manufacturer=request.form.get('manufacturer'),
                supplier=request.form.get('supplier'),
                pharmacy_id=primary_pharmacy.id if primary_pharmacy else None
            )
            
            expiry_date_str = request.form.get('expiry_date')
            if expiry_date_str:
                product.expiry_date = datetime.strptime(expiry_date_str, '%Y-%m-%d').date()
            
            db.session.add(product)
            db.session.flush()
            
            audit = Audit(
                user_id=current_user.id,
                action='create_product',
                entity_type='product',
                entity_id=product.id,
                details=f'Produit créé: {product.name}',
                ip_address=request.remote_addr
            )
            db.session.add(audit)
            
            db.session.commit()
            
            flash('Produit ajouté avec succès!', 'success')
            return redirect(url_for('products.index'))
        except Exception as e:
            db.session.rollback()
            flash(f'Erreur: {str(e)}', 'danger')
    
    return render_template('products/add.html')

@products_bp.route('/edit/<int:id>', methods=['GET', 'POST'])
@require_permission('manage_products')
def edit(id):
    product = Product.query.get_or_404(id)
    
    if request.method == 'POST':
        try:
            product.name = request.form.get('name')
            product.description = request.form.get('description')
            product.barcode = request.form.get('barcode')
            product.category = request.form.get('category')
            product.unit = request.form.get('unit', 'piece')
            product.purchase_price = float(request.form.get('purchase_price', 0))
            product.selling_price = float(request.form.get('selling_price', 0))
            product.wholesale_price = float(request.form.get('wholesale_price', 0))
            product.min_stock_level = int(request.form.get('min_stock_level', 10))
            product.manufacturer = request.form.get('manufacturer')
            product.supplier = request.form.get('supplier')
            
            expiry_date_str = request.form.get('expiry_date')
            if expiry_date_str:
                product.expiry_date = datetime.strptime(expiry_date_str, '%Y-%m-%d').date()
            
            audit = Audit(
                user_id=current_user.id,
                action='update_product',
                entity_type='product',
                entity_id=product.id,
                details=f'Produit modifié: {product.name}',
                ip_address=request.remote_addr
            )
            db.session.add(audit)
            
            db.session.commit()
            
            flash('Produit modifié avec succès!', 'success')
            return redirect(url_for('products.index'))
        except Exception as e:
            db.session.rollback()
            flash(f'Erreur: {str(e)}', 'danger')
    
    return render_template('products/edit.html', product=product)

@products_bp.route('/delete/<int:id>', methods=['POST'])
@require_permission('manage_products')
def delete(id):
    product = Product.query.get_or_404(id)
    
    try:
        product.is_active = False
        
        audit = Audit(
            user_id=current_user.id,
            action='delete_product',
            entity_type='product',
            entity_id=product.id,
            details=f'Produit supprimé: {product.name}',
            ip_address=request.remote_addr
        )
        db.session.add(audit)
        
        db.session.commit()
        flash('Produit supprimé avec succès!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erreur: {str(e)}', 'danger')
    
    return redirect(url_for('products.index'))

@products_bp.route('/alerts')
@require_permission('manage_products')
def alerts():
    today = datetime.now().date()
    pharmacy_filter = request.args.get('pharmacy_id', 'all')
    
    # Requête pour le stock faible
    low_stock_query = Product.query.filter(
        Product.is_active == True,
        Product.stock_quantity <= Product.min_stock_level
    )
    low_stock_query = filter_by_pharmacy(low_stock_query, Product, pharmacy_filter)
    low_stock = low_stock_query.all()
    
    # Requête pour les produits expirés
    expired_query = Product.query.filter(
        Product.is_active == True,
        Product.expiry_date < today
    )
    expired_query = filter_by_pharmacy(expired_query, Product, pharmacy_filter)
    expired = expired_query.all()
    
    pharmacies = get_accessible_pharmacies() if is_admin() else []
    
    return render_template('products/alerts.html', 
                         low_stock=low_stock, 
                         expired=expired,
                         pharmacies=pharmacies,
                         pharmacy_filter=pharmacy_filter)

@products_bp.route('/export/<format>')
@require_permission('manage_products')
def export(format):
    """Exporte la liste des produits en CSV ou Excel"""
    pharmacy_filter = request.args.get('pharmacy_id', 'all')
    search = request.args.get('search', '')
    
    query = Product.query.filter_by(is_active=True)
    query = filter_by_pharmacy(query, Product, pharmacy_filter)
    
    if search:
        query = query.filter(
            db.or_(
                Product.name.ilike(f'%{search}%'),
                Product.barcode.ilike(f'%{search}%'),
                Product.category.ilike(f'%{search}%')
            )
        )
    
    products = query.order_by(Product.name).all()
    
    # Préparer les données
    headers = ['ID', 'Nom', 'Code-barres', 'Forme', 'Prix Achat', 'Prix Vente', 
               'Prix Gros', 'Stock', 'Stock Min', 'Unité', 'Fabricant', 'Pharmacie']
    
    data = []
    for p in products:
        pharmacy_name = p.pharmacy.name if p.pharmacy else 'N/A'
        data.append({
            'ID': p.id,
            'Nom': p.name,
            'Code-barres': p.barcode or '',
            'Forme': p.category or '',
            'Prix Achat': p.purchase_price,
            'Prix Vente': p.selling_price,
            'Prix Gros': p.wholesale_price,
            'Stock': p.stock_quantity,
            'Stock Min': p.min_stock_level,
            'Unité': p.unit,
            'Fabricant': p.manufacturer or '',
            'Pharmacie': pharmacy_name
        })
    
    if format == 'csv':
        return export_to_csv(data, 'produits', headers)
    elif format == 'excel':
        return export_to_excel(data, 'produits', headers, 'Produits')
    else:
        flash('Format non supporté', 'danger')
        return redirect(url_for('products.index'))

@products_bp.route('/import', methods=['GET', 'POST'])
@require_permission('manage_products')
def import_products():
    """Importe des produits depuis un fichier CSV"""
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('Aucun fichier sélectionné', 'danger')
            return redirect(url_for('products.import_products'))
        
        file = request.files['file']
        if file.filename == '':
            flash('Aucun fichier sélectionné', 'danger')
            return redirect(url_for('products.import_products'))
        
        if not file.filename.endswith('.csv'):
            flash('Seuls les fichiers CSV sont acceptés', 'danger')
            return redirect(url_for('products.import_products'))
        
        try:
            # Parser le CSV
            data = parse_csv_file(file)
            
            if data is None:
                return redirect(url_for('products.import_products'))
            
            # Valider les données
            required_fields = ['Nom', 'Prix Vente']
            valid, errors = validate_import_data(data, required_fields)
            
            if not valid:
                for error in errors:
                    flash(error, 'danger')
                return redirect(url_for('products.import_products'))
            
            # Importer les produits
            primary_pharmacy = current_user.get_primary_pharmacy()
            imported_count = 0
            
            for row in data:
                try:
                    product = Product(
                        name=row['Nom'],
                        description=row.get('Description', ''),
                        barcode=row.get('Code-barres', ''),
                        category=row.get('Forme', ''),
                        unit=row.get('Unité', 'piece'),
                        purchase_price=float(row.get('Prix Achat', 0)),
                        selling_price=float(row.get('Prix Vente', 0)),
                        wholesale_price=float(row.get('Prix Gros', 0)),
                        stock_quantity=int(row.get('Stock', 0)),
                        min_stock_level=int(row.get('Stock Min', 10)),
                        manufacturer=row.get('Fabricant', ''),
                        supplier=row.get('Fournisseur', ''),
                        pharmacy_id=primary_pharmacy.id if primary_pharmacy else None
                    )
                    
                    db.session.add(product)
                    imported_count += 1
                except Exception as e:
                    flash(f'Erreur ligne "{row.get("Nom", "?")}": {str(e)}', 'warning')
                    continue
            
            # Audit
            audit = Audit(
                user_id=current_user.id,
                action='import_products',
                entity_type='product',
                details=f'{imported_count} produits importés',
                ip_address=request.remote_addr
            )
            db.session.add(audit)
            
            db.session.commit()
            flash(f'{imported_count} produits importés avec succès!', 'success')
            
        except Exception as e:
            db.session.rollback()
            flash(f'Erreur lors de l\'import: {str(e)}', 'danger')
        
        return redirect(url_for('products.index'))
    
    return render_template('products/import.html')

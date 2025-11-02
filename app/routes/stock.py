from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from app.decorators import require_permission
from flask_login import login_required, current_user
from app.models import db, Product, StockMovement, ProductBatch, BatchMovement, Audit, Supplier
from app.pharmacy_utils import filter_by_pharmacy, get_accessible_pharmacies, is_admin
from app.export_utils import export_to_csv, export_to_excel
from datetime import datetime, timedelta
from sqlalchemy import or_, and_

stock_bp = Blueprint('stock', __name__, url_prefix='/stock')


@stock_bp.route('/')
@require_permission('manage_stock')
def index():
    page = request.args.get('page', 1, type=int)
    pharmacy_filter = request.args.get('pharmacy_id', 'all')

    query = StockMovement.query.join(Product).filter(Product.is_active == True)
    
    # Filtrage par pharmacie via le produit
    if is_admin():
        if pharmacy_filter and pharmacy_filter != 'all':
            query = query.filter(Product.pharmacy_id == pharmacy_filter)
    else:
        accessible_ids = [p.id for p in get_accessible_pharmacies()]
        if accessible_ids:
            query = query.filter(Product.pharmacy_id.in_(accessible_ids))
    
    movements = query.order_by(StockMovement.created_at.desc()).paginate(
        page=page, per_page=6, error_out=False
    )
    
    pharmacies = get_accessible_pharmacies() if is_admin() else []
    return render_template('stock/index.html', movements=movements, pharmacies=pharmacies, pharmacy_filter=pharmacy_filter)

@stock_bp.route('/product-adjust/<int:product_id>', methods=['GET', 'POST'])
@require_permission('manage_stock')
def product_adjust(product_id):
    """Ajuster le stock d'un produit spécifique"""
    product = Product.query.get_or_404(product_id)
    
    if request.method == 'POST':
        try:
            adjustment_type = request.form.get('adjustment_type')
            quantity = int(request.form.get('quantity', 0))
            reason = request.form.get('reason', '')
            notes = request.form.get('notes', '')
            
            if adjustment_type == 'increase':
                product.stock_quantity += quantity
                movement_type = 'in'
            else:
                product.stock_quantity = max(0, product.stock_quantity - quantity)
                movement_type = 'out'
            
            # Créer le mouvement de stock
            movement = StockMovement(
                product_id=product.id,
                movement_type=movement_type,
                quantity=quantity,
                reference=f'AJUST-{datetime.now().strftime("%Y%m%d%H%M%S")}',
                notes=f'Ajustement: {reason}. {notes}',
                created_by=current_user.id,
                pharmacy_id=product.pharmacy_id
            )
            db.session.add(movement)
            
            # Audit
            audit = Audit(
                user_id=current_user.id,
                action='adjust_stock',
                entity_type='product',
                entity_id=product.id,
                details=f'Stock ajusté: {adjustment_type} {quantity} unités. Raison: {reason}',
                ip_address=request.remote_addr
            )
            db.session.add(audit)
            
            db.session.commit()
            flash(f'Stock ajusté avec succès!', 'success')
            return redirect(url_for('stock.product_movements', product_id=product.id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Erreur: {str(e)}', 'danger')
    
    return render_template('stock/adjust.html', product=product)



@stock_bp.route('/export/<format>')
@require_permission('manage_stock')
def export_movements(format):
    pharmacy_filter = request.args.get('pharmacy_id', 'all')
    
    query = StockMovement.query.join(Product)
    
    if is_admin():
        if pharmacy_filter and pharmacy_filter != 'all':
            query = query.filter(Product.pharmacy_id == pharmacy_filter)
    
    movements = query.order_by(StockMovement.created_at.desc()).all()
    
    headers = ['Date', 'Produit', 'Type', 'Quantité', 'Référence', 'Notes', 'Pharmacie']
    data = []
    for m in movements:
        data.append({
            'Date': m.created_at.strftime('%d/%m/%Y %H:%M'),
            'Produit': m.product.name,
            'Type': 'Entrée' if m.movement_type == 'in' else 'Sortie',
            'Quantité': m.quantity,
            'Référence': m.reference or '',
            'Notes': m.notes or '',
            'Pharmacie': m.product.pharmacy.name if m.product.pharmacy else 'N/A'
        })
    
    if format == 'csv':
        return export_to_csv(data, 'mouvements_stock', headers)
    else:
        return export_to_excel(data, 'mouvements_stock', headers, 'Stock')


@stock_bp.route('/manual-adjust', methods=['GET', 'POST'])
@require_permission('manage_stock')
def manual_adjust():
    if request.method == 'POST':
        try:
            product_id = request.form.get('product_id')
            movement_type = request.form.get('movement_type')
            quantity = int(request.form.get('quantity'))
            reference = request.form.get('reference')
            notes = request.form.get('notes')

            product = Product.query.get(product_id)
            if not product:
                flash('Produit introuvable', 'danger')
                return redirect(url_for('stock.manual_adjust'))

            if movement_type == 'in':
                product.stock_quantity += quantity
            else:
                if product.stock_quantity < quantity:
                    flash('Stock insuffisant', 'danger')
                    return redirect(url_for('stock.manual_adjust'))
                product.stock_quantity -= quantity

            movement = StockMovement(product_id=product_id,
                                     movement_type=movement_type,
                                     quantity=quantity,
                                     reference=reference,
                                     notes=notes,
                                     created_by=current_user.id)
            db.session.add(movement)

            audit = Audit(
                user_id=current_user.id,
                action='stock_adjustment',
                entity_type='stock',
                details=
                f'Ajustement stock: {product.name}, {movement_type}, {quantity}',
                ip_address=request.remote_addr)
            db.session.add(audit)

            db.session.commit()

            flash('Stock ajusté avec succès!', 'success')
            return redirect(url_for('stock.index'))
        except Exception as e:
            db.session.rollback()
            flash(f'Erreur: {str(e)}', 'danger')

    products = Product.query.filter_by(is_active=True).all()
    return render_template('stock/adjust.html', products=products)


@stock_bp.route('/batches')
@require_permission('manage_stock')
def batches():
    page = request.args.get('page', 1, type=int)
    pharmacy_filter = request.args.get('pharmacy_id', 'all')
    status_filter = request.args.get('status', 'all')
    search = request.args.get('search', '')
    
    query = ProductBatch.query.join(Product)
    
    # Filtrage par pharmacie
    if is_admin():
        if pharmacy_filter and pharmacy_filter != 'all':
            query = query.filter(ProductBatch.pharmacy_id == pharmacy_filter)
    else:
        accessible_ids = [p.id for p in get_accessible_pharmacies()]
        if accessible_ids:
            query = query.filter(ProductBatch.pharmacy_id.in_(accessible_ids))
    
    # Filtrage par statut
    if status_filter and status_filter != 'all':
        query = query.filter(ProductBatch.status == status_filter)
    
    # Recherche par numéro de lot ou nom produit
    if search:
        query = query.filter(
            or_(
                ProductBatch.batch_number.ilike(f'%{search}%'),
                Product.name.ilike(f'%{search}%')
            )
        )
    
    # Mettre à jour le statut de tous les lots avant affichage
    all_batches_for_update = query.all()
    for batch in all_batches_for_update:
        batch.update_status()
    db.session.commit()
    
    batches = query.order_by(ProductBatch.expiry_date.asc()).paginate(
        page=page, per_page=6, error_out=False
    )
    
    # Statistiques
    stats = {
        'total': ProductBatch.query.count(),
        'active': ProductBatch.query.filter_by(status='active').count(),
        'expiring_soon': ProductBatch.query.filter(
            and_(
                ProductBatch.expiry_date <= datetime.now().date() + timedelta(days=90),
                ProductBatch.expiry_date > datetime.now().date(),
                ProductBatch.status == 'active'
            )
        ).count(),
        'expired': ProductBatch.query.filter_by(status='expired').count(),
        'depleted': ProductBatch.query.filter_by(status='depleted').count()
    }
    
    pharmacies = get_accessible_pharmacies() if is_admin() else []
    return render_template('stock/batches.html', 
                         batches=batches, 
                         pharmacies=pharmacies,
                         pharmacy_filter=pharmacy_filter,
                         status_filter=status_filter,
                         search=search,
                         stats=stats)


@stock_bp.route('/add-batch', methods=['GET', 'POST'])
@require_permission('manage_stock')
def add_batch():
    if request.method == 'POST':
        try:
            product_id = request.form.get('product_id')
            batch_number = request.form.get('batch_number')
            quantity = int(request.form.get('quantity'))
            purchase_price = float(request.form.get('purchase_price'))
            supplier_id = request.form.get('supplier_id')
            supplier_name = request.form.get('supplier')
            pharmacy_id = request.form.get('pharmacy_id')

            product = Product.query.get(product_id)
            if not product:
                flash('Produit introuvable', 'danger')
                return redirect(url_for('stock.add_batch'))

            # Vérifier si le lot existe déjà
            existing_batch = ProductBatch.query.filter_by(
                product_id=product_id,
                batch_number=batch_number,
                pharmacy_id=pharmacy_id
            ).first()
            
            if existing_batch:
                flash(f'Un lot avec le numéro {batch_number} existe déjà pour ce produit', 'warning')
                return redirect(url_for('stock.add_batch'))

            batch = ProductBatch(
                product_id=product_id,
                pharmacy_id=pharmacy_id or product.pharmacy_id,
                batch_number=batch_number,
                quantity=quantity,
                initial_quantity=quantity,
                purchase_price=purchase_price,
                unit_cost=purchase_price,
                supplier_id=supplier_id if supplier_id else None,
                supplier=supplier_name,
                status='active'
            )

            # Dates
            expiry_date_str = request.form.get('expiry_date')
            if expiry_date_str:
                batch.expiry_date = datetime.strptime(expiry_date_str, '%Y-%m-%d').date()
            
            manufacture_date_str = request.form.get('manufacture_date')
            if manufacture_date_str:
                batch.manufacture_date = datetime.strptime(manufacture_date_str, '%Y-%m-%d').date()

            db.session.add(batch)
            db.session.flush()

            # Créer mouvement de lot
            batch_movement = BatchMovement(
                batch_id=batch.id,
                movement_type='entry',
                quantity=quantity,
                reference_type='purchase',
                user_id=current_user.id,
                notes=f'Réception lot {batch_number}'
            )
            db.session.add(batch_movement)

            # Mettre à jour le stock produit
            product.stock_quantity += quantity

            # Créer mouvement de stock
            movement = StockMovement(
                product_id=product_id,
                movement_type='in',
                quantity=quantity,
                reference=f'Lot: {batch_number}',
                notes=f'Ajout de lot {batch_number}',
                created_by=current_user.id
            )
            db.session.add(movement)

            # Audit
            audit = Audit(
                user_id=current_user.id,
                action='add_batch',
                entity_type='batch',
                details=f'Lot ajouté: {batch_number} pour {product.name} ({quantity} unités)',
                ip_address=request.remote_addr
            )
            db.session.add(audit)

            db.session.commit()

            flash('Lot ajouté avec succès!', 'success')
            return redirect(url_for('stock.batches'))
        except Exception as e:
            db.session.rollback()
            flash(f'Erreur: {str(e)}', 'danger')

    from app.models import Pharmacy
    products = Product.query.filter_by(is_active=True).all()
    suppliers = Supplier.query.filter_by(is_active=True).all()
    pharmacies = get_accessible_pharmacies()
    
    return render_template('stock/add_batch.html', 
                         products=products, 
                         suppliers=suppliers,
                         pharmacies=pharmacies)


@stock_bp.route('/transfer', methods=['GET', 'POST'])
@require_permission('manage_stock')
def transfer():
    if request.method == 'POST':
        try:
            product_id = request.form.get('product_id')
            from_pharmacy_id = int(request.form.get('from_pharmacy_id'))
            to_pharmacy_id = int(request.form.get('to_pharmacy_id'))
            quantity = int(request.form.get('quantity'))
            notes = request.form.get('notes', '')
            
            if from_pharmacy_id == to_pharmacy_id:
                flash('Les pharmacies source et destination doivent être différentes', 'danger')
                return redirect(url_for('stock.transfer'))
            
            from app.models import Pharmacy
            product = Product.query.get(product_id)
            from_pharmacy = Pharmacy.query.get(from_pharmacy_id)
            to_pharmacy = Pharmacy.query.get(to_pharmacy_id)
            
            if not product or not from_pharmacy or not to_pharmacy:
                flash('Produit ou pharmacie introuvable', 'danger')
                return redirect(url_for('stock.transfer'))
            
            if product.pharmacy_id != from_pharmacy_id:
                flash('Ce produit n\'appartient pas à la pharmacie source', 'danger')
                return redirect(url_for('stock.transfer'))
            
            if product.stock_quantity < quantity:
                flash('Stock insuffisant dans la pharmacie source', 'danger')
                return redirect(url_for('stock.transfer'))
            
            reference = f'TRANS-{datetime.now().strftime("%Y%m%d")}-{product.id}'
            
            movement_out = StockMovement(
                product_id=product.id,
                pharmacy_id=from_pharmacy_id,
                movement_type='transfer_out',
                quantity=quantity,
                reference=reference,
                notes=f'Transfert vers {to_pharmacy.name}: {notes}',
                created_by=current_user.id
            )
            db.session.add(movement_out)
            
            product.stock_quantity -= quantity
            
            product_in_dest = Product.query.filter_by(
                barcode=product.barcode,
                pharmacy_id=to_pharmacy_id
            ).first()
            
            if not product_in_dest:
                product_in_dest = Product(
                    name=product.name,
                    description=product.description,
                    barcode=product.barcode,
                    category=product.category,
                    unit=product.unit,
                    purchase_price=product.purchase_price,
                    selling_price=product.selling_price,
                    wholesale_price=product.wholesale_price,
                    stock_quantity=quantity,
                    min_stock_level=product.min_stock_level,
                    expiry_date=product.expiry_date,
                    manufacturer=product.manufacturer,
                    supplier=product.supplier,
                    pharmacy_id=to_pharmacy_id,
                    is_active=True
                )
                db.session.add(product_in_dest)
                db.session.flush()
            else:
                product_in_dest.stock_quantity += quantity
            
            movement_in = StockMovement(
                product_id=product_in_dest.id,
                pharmacy_id=to_pharmacy_id,
                movement_type='transfer_in',
                quantity=quantity,
                reference=reference,
                notes=f'Transfert depuis {from_pharmacy.name}: {notes}',
                created_by=current_user.id
            )
            db.session.add(movement_in)
            
            audit = Audit(
                user_id=current_user.id,
                action='stock_transfer',
                entity_type='stock',
                details=f'Transfert: {product.name} x{quantity} de {from_pharmacy.name} vers {to_pharmacy.name}',
                ip_address=request.remote_addr
            )
            db.session.add(audit)
            
            db.session.commit()
            
            flash(f'Transfert effectué avec succès! {quantity} unités de {product.name} transférées.', 'success')
            return redirect(url_for('stock.index'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Erreur: {str(e)}', 'danger')
    
    from app.models import Pharmacy
    pharmacies = Pharmacy.query.filter_by(is_active=True).all()
    products = Product.query.filter_by(is_active=True).all()
    
    return render_template('stock/transfer.html', pharmacies=pharmacies, products=products)


# ===== NOUVELLES ROUTES LOTS =====

@stock_bp.route('/batches/<int:id>')
@require_permission('manage_stock')
def batch_view(id):
    """Vue détaillée d'un lot"""
    batch = ProductBatch.query.get_or_404(id)
    batch.update_status()
    db.session.commit()
    
    # Récupérer l'historique des mouvements
    movements = BatchMovement.query.filter_by(batch_id=id).order_by(
        BatchMovement.created_at.desc()
    ).all()
    
    return render_template('stock/batch_view.html', batch=batch, movements=movements)


@stock_bp.route('/batches/<int:id>/edit', methods=['GET', 'POST'])
@require_permission('manage_stock')
def batch_edit(id):
    """Éditer un lot"""
    batch = ProductBatch.query.get_or_404(id)
    
    if request.method == 'POST':
        try:
            # On ne peut modifier que certains champs
            batch.supplier = request.form.get('supplier')
            batch.supplier_id = request.form.get('supplier_id') or None
            
            manufacture_date_str = request.form.get('manufacture_date')
            if manufacture_date_str:
                batch.manufacture_date = datetime.strptime(manufacture_date_str, '%Y-%m-%d').date()
            
            expiry_date_str = request.form.get('expiry_date')
            if expiry_date_str:
                batch.expiry_date = datetime.strptime(expiry_date_str, '%Y-%m-%d').date()
            
            # Mettre à jour le statut
            batch.update_status()
            
            # Audit
            audit = Audit(
                user_id=current_user.id,
                action='edit_batch',
                entity_type='batch',
                details=f'Lot modifié: {batch.batch_number}',
                ip_address=request.remote_addr
            )
            db.session.add(audit)
            
            db.session.commit()
            flash('Lot modifié avec succès!', 'success')
            return redirect(url_for('stock.batch_view', id=batch.id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Erreur: {str(e)}', 'danger')
    
    suppliers = Supplier.query.filter_by(is_active=True).all()
    return render_template('stock/batch_edit.html', batch=batch, suppliers=suppliers)


@stock_bp.route('/product/<int:product_id>/movements')
@require_permission('manage_stock')
def product_movements(product_id):
    """Historique des mouvements d'un produit"""
    product = Product.query.get_or_404(product_id)
    
    page = request.args.get('page', 1, type=int)
    movements = StockMovement.query.filter_by(product_id=product_id)\
        .order_by(StockMovement.created_at.desc())\
        .paginate(page=page, per_page=20, error_out=False)
    
    return render_template('stock/product_movements.html', 
                         product=product, 
                         movements=movements)

@stock_bp.route('/batches/<int:id>/movements')
@require_permission('manage_stock')
def batch_movements(id):
    """Historique des mouvements d'un lot"""
    batch = ProductBatch.query.get_or_404(id)
    page = request.args.get('page', 1, type=int)
    
    movements = BatchMovement.query.filter_by(batch_id=id).order_by(
        BatchMovement.created_at.desc()
    ).paginate(page=page, per_page=20, error_out=False)
    
    return render_template('stock/batch_movements.html', batch=batch, movements=movements)


@stock_bp.route('/batches/expiring')
@require_permission('manage_stock')
def batches_expiring():
    """Liste des lots expirant bientôt ou expirés"""
    page = request.args.get('page', 1, type=int)
    days_filter = request.args.get('days', '90')
    pharmacy_filter = request.args.get('pharmacy_id', 'all')
    
    try:
        days = int(days_filter)
    except:
        days = 90
    
    # Lots expirant dans X jours
    expiry_threshold = datetime.now().date() + timedelta(days=days)
    
    query = ProductBatch.query.join(Product).filter(
        and_(
            ProductBatch.expiry_date <= expiry_threshold,
            ProductBatch.quantity > 0,
            ProductBatch.is_active == True
        )
    )
    
    # Filtrage par pharmacie
    if is_admin():
        if pharmacy_filter and pharmacy_filter != 'all':
            query = query.filter(ProductBatch.pharmacy_id == pharmacy_filter)
    else:
        accessible_ids = [p.id for p in get_accessible_pharmacies()]
        if accessible_ids:
            query = query.filter(ProductBatch.pharmacy_id.in_(accessible_ids))
    
    # Mettre à jour le statut
    all_batches = query.all()
    for batch in all_batches:
        batch.update_status()
    db.session.commit()
    
    batches = query.order_by(ProductBatch.expiry_date.asc()).paginate(
        page=page, per_page=20, error_out=False
    )
    
    # Statistiques
    stats = {
        'expired': ProductBatch.query.filter(
            and_(
                ProductBatch.expiry_date < datetime.now().date(),
                ProductBatch.quantity > 0
            )
        ).count(),
        'expiring_30': ProductBatch.query.filter(
            and_(
                ProductBatch.expiry_date <= datetime.now().date() + timedelta(days=30),
                ProductBatch.expiry_date > datetime.now().date(),
                ProductBatch.quantity > 0
            )
        ).count(),
        'expiring_60': ProductBatch.query.filter(
            and_(
                ProductBatch.expiry_date <= datetime.now().date() + timedelta(days=60),
                ProductBatch.expiry_date > datetime.now().date() + timedelta(days=30),
                ProductBatch.quantity > 0
            )
        ).count(),
        'expiring_90': ProductBatch.query.filter(
            and_(
                ProductBatch.expiry_date <= datetime.now().date() + timedelta(days=90),
                ProductBatch.expiry_date > datetime.now().date() + timedelta(days=60),
                ProductBatch.quantity > 0
            )
        ).count()
    }
    
    pharmacies = get_accessible_pharmacies() if is_admin() else []
    return render_template('stock/batch_alerts.html', 
                         batches=batches,
                         pharmacies=pharmacies,
                         pharmacy_filter=pharmacy_filter,
                         days_filter=days_filter,
                         stats=stats)


@stock_bp.route('/batches/export/<format>')
@require_permission('manage_stock')
def export_batches(format):
    """Exporter la liste des lots"""
    pharmacy_filter = request.args.get('pharmacy_id', 'all')
    status_filter = request.args.get('status', 'all')
    
    query = ProductBatch.query.join(Product)
    
    # Filtres
    if is_admin():
        if pharmacy_filter and pharmacy_filter != 'all':
            query = query.filter(ProductBatch.pharmacy_id == pharmacy_filter)
    
    if status_filter and status_filter != 'all':
        query = query.filter(ProductBatch.status == status_filter)
    
    batches = query.order_by(ProductBatch.expiry_date.asc()).all()
    
    headers = ['Produit', 'N° Lot', 'Pharmacie', 'Quantité Actuelle', 'Quantité Initiale', 
               'Prix Achat', 'Fournisseur', 'Date Fabrication', 'Date Expiration', 
               'Jours Restants', 'Statut']
    
    data = []
    for batch in batches:
        data.append({
            'Produit': batch.product.name,
            'N° Lot': batch.batch_number,
            'Pharmacie': batch.pharmacy.name if batch.pharmacy else 'N/A',
            'Quantité Actuelle': batch.quantity,
            'Quantité Initiale': batch.initial_quantity,
            'Prix Achat': f'${batch.purchase_price:.2f}',
            'Fournisseur': batch.supplier or 'N/A',
            'Date Fabrication': batch.manufacture_date.strftime('%d/%m/%Y') if batch.manufacture_date else 'N/A',
            'Date Expiration': batch.expiry_date.strftime('%d/%m/%Y') if batch.expiry_date else 'N/A',
            'Jours Restants': batch.days_until_expiry if batch.days_until_expiry is not None else 'N/A',
            'Statut': batch.status.upper()
        })
    
    if format == 'csv':
        return export_to_csv(data, 'lots_stock', headers)
    else:
        return export_to_excel(data, 'lots_stock', headers, 'Lots')

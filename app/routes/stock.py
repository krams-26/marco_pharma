from flask import Blueprint, render_template, request, flash, redirect, url_for
from app.decorators import require_permission
from flask_login import login_required, current_user
from app.models import db, Product, StockMovement, ProductBatch, Audit
from datetime import datetime

stock_bp = Blueprint('stock', __name__, url_prefix='/stock')

@stock_bp.route('/')
@require_permission('manage_stock')
def index():
    page = request.args.get('page', 1, type=int)
    
    movements = StockMovement.query.order_by(StockMovement.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    
    return render_template('stock/index.html', movements=movements)

@stock_bp.route('/adjust', methods=['GET', 'POST'])
@require_permission('manage_stock')
def adjust():
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
                return redirect(url_for('stock.adjust'))
            
            if movement_type == 'in':
                product.stock_quantity += quantity
            else:
                if product.stock_quantity < quantity:
                    flash('Stock insuffisant', 'danger')
                    return redirect(url_for('stock.adjust'))
                product.stock_quantity -= quantity
            
            movement = StockMovement(
                product_id=product_id,
                movement_type=movement_type,
                quantity=quantity,
                reference=reference,
                notes=notes,
                created_by=current_user.id
            )
            db.session.add(movement)
            
            audit = Audit(
                user_id=current_user.id,
                action='stock_adjustment',
                entity_type='stock',
                details=f'Ajustement stock: {product.name}, {movement_type}, {quantity}',
                ip_address=request.remote_addr
            )
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
    
    batches = ProductBatch.query.order_by(ProductBatch.received_date.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    
    return render_template('stock/batches.html', batches=batches)

@stock_bp.route('/add-batch', methods=['GET', 'POST'])
@require_permission('manage_stock')
def add_batch():
    if request.method == 'POST':
        try:
            product_id = request.form.get('product_id')
            batch_number = request.form.get('batch_number')
            quantity = int(request.form.get('quantity'))
            purchase_price = float(request.form.get('purchase_price'))
            supplier = request.form.get('supplier')
            
            product = Product.query.get(product_id)
            if not product:
                flash('Produit introuvable', 'danger')
                return redirect(url_for('stock.add_batch'))
            
            batch = ProductBatch(
                product_id=product_id,
                batch_number=batch_number,
                quantity=quantity,
                purchase_price=purchase_price,
                supplier=supplier
            )
            
            expiry_date_str = request.form.get('expiry_date')
            if expiry_date_str:
                batch.expiry_date = datetime.strptime(expiry_date_str, '%Y-%m-%d').date()
            
            product.stock_quantity += quantity
            
            movement = StockMovement(
                product_id=product_id,
                movement_type='in',
                quantity=quantity,
                reference=f'Lot: {batch_number}',
                notes=f'Ajout de lot {batch_number}',
                created_by=current_user.id
            )
            
            db.session.add(batch)
            db.session.add(movement)
            
            audit = Audit(
                user_id=current_user.id,
                action='add_batch',
                entity_type='batch',
                details=f'Lot ajouté: {batch_number} pour {product.name}',
                ip_address=request.remote_addr
            )
            db.session.add(audit)
            
            db.session.commit()
            
            flash('Lot ajouté avec succès!', 'success')
            return redirect(url_for('stock.batches'))
        except Exception as e:
            db.session.rollback()
            flash(f'Erreur: {str(e)}', 'danger')
    
    products = Product.query.filter_by(is_active=True).all()
    return render_template('stock/add_batch.html', products=products)

from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from app.models import db, Product, ProductBatch, Audit
from datetime import datetime

products_bp = Blueprint('products', __name__, url_prefix='/products')

@products_bp.route('/')
@login_required
def index():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    
    query = Product.query
    
    if search:
        query = query.filter(
            db.or_(
                Product.name.ilike(f'%{search}%'),
                Product.barcode.ilike(f'%{search}%'),
                Product.category.ilike(f'%{search}%')
            )
        )
    
    products = query.order_by(Product.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    
    return render_template('products/index.html', products=products, search=search)

@products_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add():
    if request.method == 'POST':
        try:
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
                supplier=request.form.get('supplier')
            )
            
            expiry_date_str = request.form.get('expiry_date')
            if expiry_date_str:
                product.expiry_date = datetime.strptime(expiry_date_str, '%Y-%m-%d').date()
            
            db.session.add(product)
            
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
@login_required
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
@login_required
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
@login_required
def alerts():
    today = datetime.now().date()
    
    low_stock = Product.query.filter(
        Product.is_active == True,
        Product.stock_quantity <= Product.min_stock_level
    ).all()
    
    expired = Product.query.filter(
        Product.is_active == True,
        Product.expiry_date < today
    ).all()
    
    return render_template('products/alerts.html', low_stock=low_stock, expired=expired)

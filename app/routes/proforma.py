from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from app.models import db, Proforma, ProformaItem, Customer, Product, Audit
from app.decorators import require_permission
from datetime import datetime, timedelta
import random
import string
from app.pharmacy_utils import filter_by_pharmacy, get_accessible_pharmacies, is_admin
from app.export_utils import export_to_csv, export_to_excel

proforma_bp = Blueprint('proforma', __name__, url_prefix='/proforma')

def generate_proforma_number():
    year = datetime.now().year
    count = Proforma.query.filter(
        db.extract('year', Proforma.issue_date) == year
    ).count() + 1
    return f'PROFORMA-{year}-{str(count).zfill(3)}'

@proforma_bp.route('/')
@require_permission('manage_sales')
def index():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    status = request.args.get('status', '')
    
    query = Proforma.query
    
    if search:
        query = query.filter(
            db.or_(
                Proforma.proforma_number.ilike(f'%{search}%'),
                Proforma.customer_name.ilike(f'%{search}%')
            )
        )
    
    if status:
        query = query.filter_by(status=status)
    
    proformas = query.order_by(Proforma.issue_date.desc()).paginate(
        page=page, per_page=6, error_out=False
    )
    
    return render_template('proforma/index.html', proformas=proformas, search=search, status=status)

@proforma_bp.route('/create', methods=['GET', 'POST'])
@require_permission('manage_sales')
def create():
    if request.method == 'POST':
        try:
            proforma_number = generate_proforma_number()
            
            validity_date_str = request.form.get('validity_date')
            if not validity_date_str:
                validity_date = (datetime.now() + timedelta(days=30)).date()
            else:
                validity_date = datetime.strptime(validity_date_str, '%Y-%m-%d').date()
            
            proforma = Proforma(
                proforma_number=proforma_number,
                customer_id=request.form.get('customer_id') if request.form.get('customer_id') else None,
                user_id=current_user.id,
                customer_name=request.form.get('customer_name'),
                customer_address=request.form.get('customer_address'),
                customer_phone=request.form.get('customer_phone'),
                customer_email=request.form.get('customer_email'),
                validity_date=validity_date,
                payment_conditions=request.form.get('payment_conditions', 'Paiement à la livraison'),
                delivery_conditions=request.form.get('delivery_conditions', 'Retrait en magasin'),
                notes=request.form.get('notes'),
                status='draft'
            )
            
            product_ids = request.form.getlist('product_id[]')
            quantities = request.form.getlist('quantity[]')
            prices = request.form.getlist('price[]')
            
            if not product_ids or not quantities:
                flash('Veuillez ajouter au moins un produit', 'danger')
                return redirect(url_for('proforma.create'))
            
            total_ht = 0
            for i in range(len(product_ids)):
                if product_ids[i] and quantities[i]:
                    product = Product.query.get(int(product_ids[i]))
                    if product:
                        quantity = int(quantities[i])
                        price = float(prices[i]) if prices[i] else product.selling_price
                        line_total = quantity * price
                        total_ht += line_total
                        
                        item = ProformaItem(
                            product_id=product.id,
                            product_name=product.name,
                            product_code=product.barcode or '',
                            quantity_requested=quantity,
                            stock_available=product.stock_quantity,
                            unit_price=price,
                            line_total=line_total,
                            line_notes=request.form.getlist('line_notes[]')[i] if i < len(request.form.getlist('line_notes[]')) else ''
                        )
                        proforma.items.append(item)
            
            proforma.total_ht = total_ht
            proforma.total_tax = total_ht * 0.16
            proforma.total_ttc = total_ht * 1.16
            
            db.session.add(proforma)
            db.session.flush()
            
            audit = Audit(
                user_id=current_user.id,
                action='create_proforma',
                entity_type='proforma',
                entity_id=proforma.id,
                details=f'Proforma créée: {proforma.proforma_number}',
                ip_address=request.remote_addr
            )
            db.session.add(audit)
            
            db.session.commit()
            
            flash('Facture proforma créée avec succès!', 'success')
            return redirect(url_for('proforma.show', id=proforma.id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Erreur: {str(e)}', 'danger')
            return redirect(url_for('proforma.create'))
    
    customers = Customer.query.filter_by(is_active=True).all()
    products = Product.query.filter_by(is_active=True).all()
    default_validity_date = (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')
    
    return render_template('proforma/create.html', customers=customers, products=products, default_validity_date=default_validity_date)

@proforma_bp.route('/show/<int:id>')
@require_permission('manage_sales')
def show(id):
    proforma = Proforma.query.get_or_404(id)
    return render_template('proforma/show.html', proforma=proforma)

@proforma_bp.route('/edit/<int:id>', methods=['GET', 'POST'])
@require_permission('manage_sales')
def edit(id):
    proforma = Proforma.query.get_or_404(id)
    
    if request.method == 'POST':
        try:
            validity_date_str = request.form.get('validity_date')
            if validity_date_str:
                proforma.validity_date = datetime.strptime(validity_date_str, '%Y-%m-%d').date()
            
            proforma.customer_id = request.form.get('customer_id') if request.form.get('customer_id') else None
            proforma.customer_name = request.form.get('customer_name')
            proforma.customer_address = request.form.get('customer_address')
            proforma.customer_phone = request.form.get('customer_phone')
            proforma.customer_email = request.form.get('customer_email')
            proforma.payment_conditions = request.form.get('payment_conditions')
            proforma.delivery_conditions = request.form.get('delivery_conditions')
            proforma.notes = request.form.get('notes')
            proforma.status = request.form.get('status', 'draft')
            
            ProformaItem.query.filter_by(proforma_id=id).delete()
            
            product_ids = request.form.getlist('product_id[]')
            quantities = request.form.getlist('quantity[]')
            prices = request.form.getlist('price[]')
            
            total_ht = 0
            for i in range(len(product_ids)):
                if product_ids[i] and quantities[i]:
                    product = Product.query.get(int(product_ids[i]))
                    if product:
                        quantity = int(quantities[i])
                        price = float(prices[i]) if prices[i] else product.selling_price
                        line_total = quantity * price
                        total_ht += line_total
                        
                        item = ProformaItem(
                            proforma_id=proforma.id,
                            product_id=product.id,
                            product_name=product.name,
                            product_code=product.barcode or '',
                            quantity_requested=quantity,
                            stock_available=product.stock_quantity,
                            unit_price=price,
                            line_total=line_total,
                            line_notes=request.form.getlist('line_notes[]')[i] if i < len(request.form.getlist('line_notes[]')) else ''
                        )
                        db.session.add(item)
            
            proforma.total_ht = total_ht
            proforma.total_tax = total_ht * 0.16
            proforma.total_ttc = total_ht * 1.16
            
            audit = Audit(
                user_id=current_user.id,
                action='update_proforma',
                entity_type='proforma',
                entity_id=proforma.id,
                details=f'Proforma modifiée: {proforma.proforma_number}',
                ip_address=request.remote_addr
            )
            db.session.add(audit)
            
            db.session.commit()
            
            flash('Facture proforma modifiée avec succès!', 'success')
            return redirect(url_for('proforma.show', id=proforma.id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Erreur: {str(e)}', 'danger')
    
    customers = Customer.query.filter_by(is_active=True).all()
    products = Product.query.filter_by(is_active=True).all()
    
    return render_template('proforma/edit.html', proforma=proforma, customers=customers, products=products)

@proforma_bp.route('/delete/<int:id>', methods=['POST'])
@require_permission('manage_sales')
def delete(id):
    proforma = Proforma.query.get_or_404(id)
    
    try:
        audit = Audit(
            user_id=current_user.id,
            action='delete_proforma',
            entity_type='proforma',
            entity_id=proforma.id,
            details=f'Proforma supprimée: {proforma.proforma_number}',
            ip_address=request.remote_addr
        )
        db.session.add(audit)
        
        db.session.delete(proforma)
        db.session.commit()
        
        flash('Facture proforma supprimée avec succès!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erreur: {str(e)}', 'danger')
    
    return redirect(url_for('proforma.index'))

@proforma_bp.route('/send/<int:id>', methods=['POST'])
@require_permission('manage_sales')
def send(id):
    proforma = Proforma.query.get_or_404(id)
    
    try:
        proforma.status = 'sent'
        
        audit = Audit(
            user_id=current_user.id,
            action='send_proforma',
            entity_type='proforma',
            entity_id=proforma.id,
            details=f'Proforma envoyée: {proforma.proforma_number}',
            ip_address=request.remote_addr
        )
        db.session.add(audit)
        
        db.session.commit()
        
        flash('Facture proforma envoyée au client!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erreur: {str(e)}', 'danger')
    
    return redirect(url_for('proforma.show', id=id))

@proforma_bp.route('/print/<int:id>')
@require_permission('manage_sales')
def print_proforma(id):
    proforma = Proforma.query.get_or_404(id)
    return render_template('proforma/print.html', proforma=proforma)

@proforma_bp.route('/convert-to-sale/<int:id>', methods=['POST'])
@require_permission('manage_sales')
def convert_to_sale(id):
    proforma = Proforma.query.get_or_404(id)
    
    try:
        from app.models import Sale, SaleItem
        
        invoice_number = f'INV-{datetime.now().strftime("%Y%m%d")}-{random.randint(1000, 9999)}'
        
        sale = Sale(
            invoice_number=invoice_number,
            customer_id=proforma.customer_id,
            user_id=current_user.id,
            total_amount=proforma.total_ttc,
            discount=0,
            tax=proforma.total_tax,
            paid_amount=0,
            payment_status='pending',
            notes=f'Convertie depuis proforma {proforma.proforma_number}'
        )
        
        for item in proforma.items:
            sale_item = SaleItem(
                product_id=item.product_id,
                quantity=item.quantity_requested,
                unit_price=item.unit_price,
                total=item.line_total
            )
            sale.items.append(sale_item)
        
        proforma.status = 'accepted'
        
        db.session.add(sale)
        db.session.commit()
        
        flash(f'Proforma convertie en vente {invoice_number}!', 'success')
        return redirect(url_for('sales.view', id=sale.id))
        
    except Exception as e:
        db.session.rollback()
        flash(f'Erreur lors de la conversion: {str(e)}', 'danger')
        return redirect(url_for('proforma.show', id=id))

@proforma_bp.route('/search-products')
@require_permission('manage_sales')
def search_products():
    query = request.args.get('q', '')
    if len(query) < 2:
        return jsonify([])
    
    products = Product.query.filter(
        Product.is_active == True,
        db.or_(
            Product.name.ilike(f'%{query}%'),
            Product.barcode.ilike(f'%{query}%')
        )
    ).limit(20).all()
    
    return jsonify([{
        'id': p.id,
        'name': p.name,
        'code': p.barcode or '',
        'stock': p.stock_quantity,
        'price': p.selling_price
    } for p in products])


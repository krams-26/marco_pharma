from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from app.models import db, Product, Customer, Sale, SaleItem, Payment, StockMovement, Audit
from app.decorators import require_permission
from datetime import datetime
import random
import string

pos_bp = Blueprint('pos', __name__, url_prefix='/pos')

def generate_invoice_number():
    date_str = datetime.now().strftime('%Y%m%d')
    random_str = ''.join(random.choices(string.digits, k=4))
    return f'INV-{date_str}-{random_str}'

@pos_bp.route('/')
@require_permission('manage_sales')
def index():
    products = Product.query.filter_by(is_active=True).all()
    customers = Customer.query.filter_by(is_active=True).all()
    return render_template('pos/index.html', products=products, customers=customers)

@pos_bp.route('/search-product')
@require_permission('manage_sales')
def search_product():
    query = request.args.get('q', '')
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
        'barcode': p.barcode,
        'price': p.selling_price,
        'stock': p.stock_quantity
    } for p in products])

@pos_bp.route('/create-sale', methods=['POST'])
@require_permission('manage_sales')
def create_sale():
    try:
        data = request.get_json()
        
        customer_id = data.get('customer_id')
        items = data.get('items', [])
        discount = float(data.get('discount', 0))
        paid_amount = float(data.get('paid_amount', 0))
        payment_method = data.get('payment_method', 'cash')
        notes = data.get('notes', '')
        
        if not items:
            return jsonify({'success': False, 'message': 'Aucun article dans la vente'}), 400
        
        invoice_number = generate_invoice_number()
        
        sale = Sale(
            invoice_number=invoice_number,
            customer_id=customer_id if customer_id else None,
            user_id=current_user.id,
            discount=discount,
            payment_method=payment_method,
            notes=notes
        )
        
        total_amount = 0
        for item_data in items:
            product = Product.query.get(item_data['product_id'])
            if not product:
                return jsonify({'success': False, 'message': f'Produit introuvable'}), 404
            
            if product.stock_quantity < item_data['quantity']:
                return jsonify({'success': False, 'message': f'Stock insuffisant pour {product.name}'}), 400
            
            item_total = item_data['quantity'] * item_data['price']
            total_amount += item_total
            
            sale_item = SaleItem(
                product_id=product.id,
                quantity=item_data['quantity'],
                unit_price=item_data['price'],
                total=item_total
            )
            sale.items.append(sale_item)
            
            product.stock_quantity -= item_data['quantity']
            
            movement = StockMovement(
                product_id=product.id,
                movement_type='out',
                quantity=item_data['quantity'],
                reference=invoice_number,
                notes=f'Vente {invoice_number}',
                created_by=current_user.id
            )
            db.session.add(movement)
        
        sale.total_amount = total_amount - discount
        sale.paid_amount = paid_amount
        
        if paid_amount >= sale.total_amount:
            sale.payment_status = 'paid'
        elif paid_amount > 0:
            sale.payment_status = 'partial'
        else:
            sale.payment_status = 'pending'
        
        db.session.add(sale)
        db.session.flush()
        
        if paid_amount > 0:
            payment = Payment(
                sale_id=sale.id,
                customer_id=customer_id if customer_id else None,
                amount=paid_amount,
                payment_method=payment_method
            )
            db.session.add(payment)
        
        audit = Audit(
            user_id=current_user.id,
            action='create_sale',
            entity_type='sale',
            entity_id=sale.id,
            details=f'Vente créée: {invoice_number}, Total: {sale.total_amount}',
            ip_address=request.remote_addr
        )
        db.session.add(audit)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Vente créée avec succès',
            'invoice_number': invoice_number,
            'sale_id': sale.id
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@pos_bp.route('/invoice/<int:sale_id>')
@require_permission('manage_sales')
def invoice(sale_id):
    sale = Sale.query.get_or_404(sale_id)
    return render_template('pos/invoice.html', sale=sale)

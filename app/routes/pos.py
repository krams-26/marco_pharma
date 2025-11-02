from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from app.models import db, Product, Customer, Sale, SaleItem, Payment, StockMovement, Audit, TempSale, ProductBatch, BatchMovement, ExchangeRate
from app.decorators import require_permission
from app.pharmacy_utils import filter_by_pharmacy
from datetime import datetime
from sqlalchemy import and_
import random
import string
import json

pos_bp = Blueprint('pos', __name__, url_prefix='/pos')

def generate_invoice_number():
    date_str = datetime.now().strftime('%Y%m%d')
    random_str = ''.join(random.choices(string.digits, k=4))
    return f'INV-{date_str}-{random_str}'


def get_best_batch_fefo(product_id, pharmacy_id, quantity_needed):
    """
    Sélectionner les meilleurs lots selon FEFO (First Expired First Out)
    
    Args:
        product_id: ID du produit
        pharmacy_id: ID de la pharmacie
        quantity_needed: Quantité nécessaire
    
    Returns:
        Liste de tuples (batch, quantity_to_take) ou None si stock insuffisant
    """
    # Récupérer tous les lots actifs du produit, triés par date d'expiration (FEFO)
    available_batches = ProductBatch.query.filter(
        and_(
            ProductBatch.product_id == product_id,
            ProductBatch.pharmacy_id == pharmacy_id,
            ProductBatch.status == 'active',
            ProductBatch.quantity > 0,
            ProductBatch.is_active == True
        )
    ).order_by(
        ProductBatch.expiry_date.asc(),  # Plus ancien expire en premier
        ProductBatch.received_date.asc()  # Si même expiration, plus ancien reçu en premier
    ).all()
    
    if not available_batches:
        return None
    
    # Calculer quantité totale disponible
    total_available = sum(batch.quantity for batch in available_batches)
    if total_available < quantity_needed:
        return None  # Stock insuffisant
    
    # Répartir la quantité sur les lots selon FEFO
    batches_to_use = []
    remaining_quantity = quantity_needed
    
    for batch in available_batches:
        if remaining_quantity <= 0:
            break
        
        # Ne pas utiliser les lots expirés
        if batch.is_expired:
            continue
        
        quantity_from_batch = min(batch.quantity, remaining_quantity)
        batches_to_use.append((batch, quantity_from_batch))
        remaining_quantity -= quantity_from_batch
    
    return batches_to_use if remaining_quantity <= 0 else None

@pos_bp.route('/')
@require_permission('manage_sales')
def index():
    # Filtrer les produits selon le scope utilisateur
    products_query = Product.query.filter_by(is_active=True)
    products_query = filter_by_pharmacy(products_query, Product)
    products = products_query.all()
    
    customers = Customer.query.filter_by(is_active=True).all()
    
    # Récupérer le taux de change actif
    exchange_rate = ExchangeRate.query.filter_by(
        from_currency='USD',
        to_currency='CDF'
    ).first()
    
    rate = exchange_rate.rate if exchange_rate else 2800  # Valeur par défaut
    
    return render_template('pos/index.html', products=products, customers=customers, exchange_rate=rate)

@pos_bp.route('/search-product')
@require_permission('manage_sales')
def search_product():
    query = request.args.get('q', '')
    
    if not query:
        return jsonify([])
    
    # Créer la requête de base
    products_query = Product.query.filter(
        Product.is_active == True,
        db.or_(
            Product.name.ilike(f'%{query}%'),
            Product.barcode.ilike(f'%{query}%')
        )
    )
    
    # Filtrer selon le scope utilisateur (pharmacy ou personal)
    products_query = filter_by_pharmacy(products_query, Product)
    
    # Appliquer la limite APRÈS le filtrage
    products = products_query.limit(20).all()
    
    return jsonify([{
        'id': p.id,
        'name': p.name,
        'barcode': p.barcode,
        'category': p.category,
        'purchase_price': p.purchase_price,
        'price': p.selling_price,
        'wholesale_price': p.wholesale_price,
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
        payment_type = data.get('payment_type', 'cash')
        notes = data.get('notes', '')
        
        if not items:
            return jsonify({'success': False, 'message': 'Aucun article dans la vente'}), 400
        
        primary_pharmacy = current_user.get_primary_pharmacy()
        
        # Si vendeur : créer vente temporaire en attente de validation
        if current_user.role == 'vendeur':
            reference = generate_invoice_number()
            
            total_amount = sum(item['quantity'] * item['price'] for item in items)
            
            temp_sale = TempSale(
                reference=reference,
                customer_id=customer_id if customer_id else None,
                created_by=current_user.id,
                pharmacy_id=primary_pharmacy.id if primary_pharmacy else None,
                total_amount=total_amount - discount,
                discount=discount,
                items_data=json.dumps(items),
                payment_method=payment_method,
                notes=notes,
                status='pending'
            )
            
            db.session.add(temp_sale)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'Vente créée en attente de validation',
                'reference': reference,
                'temp_sale_id': temp_sale.id,
                'is_temp': True
            })
        
        # Caissier/Manager/Admin : créer vente directement
        invoice_number = generate_invoice_number()
        
        sale = Sale(
            invoice_number=invoice_number,
            customer_id=customer_id if customer_id else None,
            user_id=current_user.id,
            pharmacy_id=primary_pharmacy.id if primary_pharmacy else None,
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
            
            # Déduire le stock du produit
            product.stock_quantity -= item_data['quantity']
            
            # FEFO: Sélectionner les meilleurs lots et enregistrer les mouvements
            batches_to_use = get_best_batch_fefo(
                product.id,
                primary_pharmacy.id if primary_pharmacy else None,
                item_data['quantity']
            )
            
            if batches_to_use:
                # Déduire des lots selon FEFO
                for batch, quantity_from_batch in batches_to_use:
                    batch.quantity -= quantity_from_batch
                    batch.update_status()  # Mettre à jour le statut si épuisé
                    
                    # Enregistrer mouvement de lot
                    batch_movement = BatchMovement(
                        batch_id=batch.id,
                        movement_type='sale',
                        quantity=quantity_from_batch,
                        reference_type='sale',
                        reference_id=None,  # Sera mis à jour après commit
                        user_id=current_user.id,
                        notes=f'Vente {invoice_number} - {product.name}'
                    )
                    db.session.add(batch_movement)
            
            # Créer mouvement de stock global
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
        sale.payment_type = payment_type
        sale.remaining_amount = sale.total_amount - paid_amount
        
        if payment_type == 'credit':
            if paid_amount >= sale.total_amount:
                sale.credit_status = 'paid'
                sale.payment_status = 'paid'
            elif paid_amount > 0:
                sale.credit_status = 'partially_paid'
                sale.payment_status = 'partial'
            else:
                sale.credit_status = 'unpaid'
                sale.payment_status = 'pending'
        else:
            if paid_amount >= sale.total_amount:
                sale.payment_status = 'paid'
            elif paid_amount > 0:
                sale.payment_status = 'partial'
            else:
                sale.payment_status = 'pending'
        
        db.session.add(sale)
        db.session.flush()
        
        # Mettre à jour les reference_id des mouvements de lots avec le sale.id
        BatchMovement.query.filter(
            and_(
                BatchMovement.reference_type == 'sale',
                BatchMovement.reference_id == None,
                BatchMovement.user_id == current_user.id
            )
        ).update({'reference_id': sale.id}, synchronize_session='fetch')
        
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

"""
Routes API pour tous les modals de l'application
Centralisation pour meilleure maintenance
"""
from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from app.models import db, Sale, Product, StockMovement, Task, Notification, Proforma, Supplier, ProductBatch
from app.decorators import require_permission
from datetime import datetime

api_modals_bp = Blueprint('api_modals', __name__, url_prefix='/api')

# ============ VENTES ============
@api_modals_bp.route('/sales/<int:id>/quick-edit', methods=['POST'])
@login_required
def quick_edit_sale(id):
    try:
        data = request.get_json()
        sale = Sale.query.get_or_404(id)
        
        sale.discount = float(data.get('discount', 0))
        sale.notes = data.get('notes', '')
        sale.total_amount = sum(item.total for item in sale.items) - sale.discount
        
        db.session.commit()
        return jsonify({'success': True, 'message': 'Vente modifiée'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

# ============ STOCK ============
@api_modals_bp.route('/stock/quick-adjust', methods=['POST'])
@login_required
def quick_adjust_stock():
    try:
        data = request.get_json()
        product = Product.query.get_or_404(data['product_id'])
        
        quantity = int(data['quantity'])
        adj_type = data['type']
        
        if adj_type == 'in':
            product.stock_quantity += quantity
        else:
            product.stock_quantity -= quantity
        
        movement = StockMovement(
            product_id=product.id,
            movement_type=adj_type,
            quantity=quantity,
            reference=data.get('reference', ''),
            notes=data.get('notes', ''),
            created_by=current_user.id
        )
        db.session.add(movement)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Stock ajusté', 'new_stock': product.stock_quantity})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@api_modals_bp.route('/stock/alerts')
@login_required
def stock_alerts():
    try:
        low_stock = Product.query.filter(
            Product.stock_quantity <= Product.min_stock_level,
            Product.is_active == True
        ).all()
        
        return jsonify({
            'products': [{
                'id': p.id,
                'name': p.name,
                'current_stock': p.stock_quantity,
                'min_level': p.min_stock_level,
                'difference': p.min_stock_level - p.stock_quantity
            } for p in low_stock]
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@api_modals_bp.route('/products/<int:id>/quick-price', methods=['POST'])
@login_required
def quick_update_price(id):
    try:
        data = request.get_json()
        product = Product.query.get_or_404(id)
        product.selling_price = float(data['new_price'])
        db.session.commit()
        return jsonify({'success': True, 'message': 'Prix mis à jour'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@api_modals_bp.route('/batches/<int:id>')
@login_required
def batch_details(id):
    try:
        batch = ProductBatch.query.get_or_404(id)
        return jsonify({
            'batch_number': batch.batch_number,
            'product_name': batch.product.name if batch.product else 'N/A',
            'quantity': batch.quantity,
            'received_date': batch.received_date.strftime('%d/%m/%Y') if batch.received_date else 'N/A',
            'expiry_date': batch.expiry_date.strftime('%d/%m/%Y') if batch.expiry_date else 'N/A',
            'supplier': batch.supplier or 'N/A',
            'purchase_price': batch.purchase_price,
            'notes': batch.notes or ''
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

# ============ TÂCHES ============
@api_modals_bp.route('/tasks/<int:id>/status', methods=['POST'])
@login_required
def update_task_status(id):
    try:
        data = request.get_json()
        task = Task.query.get_or_404(id)
        task.status = data['status']
        if data['status'] == 'completed':
            task.completed_at = datetime.utcnow()
        db.session.commit()
        return jsonify({'success': True, 'message': 'Statut mis à jour'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@api_modals_bp.route('/tasks/<int:id>')
@login_required
def task_details(id):
    try:
        task = Task.query.get_or_404(id)
        return jsonify({
            'title': task.title,
            'description': task.description or '',
            'priority': task.priority,
            'status': task.status,
            'assigned_to': task.assigned_user.full_name if task.assigned_user else 'Non assigné',
            'assigned_by': task.assigner.full_name if task.assigner else 'N/A',
            'due_date': task.due_date.strftime('%d/%m/%Y') if task.due_date else 'Aucune',
            'created_at': task.created_at.strftime('%d/%m/%Y %H:%M'),
            'is_overdue': task.is_overdue if hasattr(task, 'is_overdue') else False
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

# ============ NOTIFICATIONS ============
@api_modals_bp.route('/notifications/<int:id>')
@login_required
def notification_details(id):
    try:
        notif = Notification.query.get_or_404(id)
        notif.is_read = True
        db.session.commit()
        return jsonify({
            'title': notif.title,
            'message': notif.message,
            'created_at': notif.created_at.strftime('%d/%m/%Y %H:%M'),
            'sender': notif.sender.full_name if hasattr(notif, 'sender') and notif.sender else 'Système'
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@api_modals_bp.route('/notifications/create', methods=['POST'])
@login_required
def create_notification():
    try:
        data = request.get_json()
        users = data.get('users', [])
        
        if 'all' in users:
            from app.models import User
            users = [u.id for u in User.query.filter_by(is_active=True).all()]
        
        for user_id in users:
            notif = Notification(
                user_id=int(user_id),
                title=data['title'],
                message=data['message'],
                is_read=False
            )
            db.session.add(notif)
        
        db.session.commit()
        return jsonify({'success': True, 'message': f'{len(users)} notification(s) envoyée(s)'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

# ============ PROFORMA ============
@api_modals_bp.route('/proforma/<int:id>')
@login_required
def proforma_preview(id):
    try:
        proforma = Proforma.query.get_or_404(id)
        return jsonify({
            'reference': proforma.reference,
            'customer': proforma.customer.name if proforma.customer else 'Anonyme',
            'date': proforma.created_at.strftime('%d/%m/%Y'),
            'valid_until': proforma.valid_until.strftime('%d/%m/%Y') if proforma.valid_until else 'N/A',
            'items': [{
                'product': item.product.name if item.product else 'N/A',
                'quantity': item.quantity,
                'price': item.unit_price,
                'total': item.total
            } for item in proforma.items],
            'discount': proforma.discount,
            'total': proforma.total_amount
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@api_modals_bp.route('/proforma/<int:id>/convert', methods=['POST'])
@login_required
def convert_proforma(id):
    try:
        data = request.get_json()
        proforma = Proforma.query.get_or_404(id)
        
        if proforma.status != 'pending':
            return jsonify({'success': False, 'message': 'Proforma déjà convertie'}), 400
        
        from app.models import SaleItem
        from random import randint
        
        # Créer la vente
        sale = Sale(
            invoice_number=f"INV{datetime.now().strftime('%Y%m%d')}{randint(1000, 9999)}",
            customer_id=proforma.customer_id,
            user_id=current_user.id,
            pharmacy_id=proforma.pharmacy_id,
            discount=proforma.discount,
            payment_method=data.get('payment_method', 'cash')
        )
        db.session.add(sale)
        db.session.flush()
        
        # Copier les items
        for item in proforma.items:
            sale_item = SaleItem(
                sale_id=sale.id,
                product_id=item.product_id,
                quantity=item.quantity,
                unit_price=item.unit_price
            )
            db.session.add(sale_item)
        
        proforma.status = 'converted'
        proforma.converted_sale_id = sale.id
        
        db.session.commit()
        return jsonify({'success': True, 'message': 'Proforma convertie en vente', 'sale_id': sale.id})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

# ============ FOURNISSEURS ============
@api_modals_bp.route('/suppliers/<int:id>')
@login_required
def supplier_details(id):
    try:
        supplier = Supplier.query.get_or_404(id)
        products = Product.query.filter_by(supplier_id=supplier.id).all()
        
        return jsonify({
            'name': supplier.name,
            'email': supplier.email or 'N/A',
            'phone': supplier.phone or 'N/A',
            'address': supplier.address or 'N/A',
            'contact_person': supplier.contact_person or 'N/A',
            'products_count': len(products),
            'products': [{
                'id': p.id,
                'name': p.name,
                'stock': p.stock_quantity
            } for p in products[:10]]
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


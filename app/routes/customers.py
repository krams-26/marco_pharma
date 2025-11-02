from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from app.decorators import require_permission
from flask_login import login_required, current_user
from app.models import db, Customer, Sale, Payment, Audit, SaleItem
from app.pharmacy_utils import filter_by_pharmacy, get_accessible_pharmacies, is_admin
from app.export_utils import export_to_csv, export_to_excel
from sqlalchemy import func

customers_bp = Blueprint('customers', __name__, url_prefix='/customers')

# ========== ROUTES API POUR MODALS ==========

@customers_bp.route('/quick-view/<int:id>')
@login_required
def quick_view(id):
    """Vue rapide d'un client avec historique d'achats"""
    customer = Customer.query.get_or_404(id)
    
    # Récupérer les dernières ventes
    recent_sales = Sale.query.filter_by(customer_id=customer.id).order_by(Sale.sale_date.desc()).limit(5).all()
    
    # Statistiques
    total_sales = Sale.query.filter_by(customer_id=customer.id).count()
    total_amount = db.session.query(func.sum(Sale.total_amount)).filter_by(customer_id=customer.id).scalar() or 0
    total_paid = db.session.query(func.sum(Sale.paid_amount)).filter_by(customer_id=customer.id).scalar() or 0
    balance_due = total_amount - total_paid
    
    return jsonify({
        'id': customer.id,
        'name': customer.name,
        'email': customer.email,
        'phone': customer.phone,
        'address': customer.address,
        'customer_type': customer.customer_type,
        'credit_limit': customer.credit_limit,
        'is_active': customer.is_active,
        'total_sales': total_sales,
        'total_amount': float(total_amount),
        'total_paid': float(total_paid),
        'balance_due': float(balance_due),
        'recent_sales': [{
            'id': sale.id,
            'invoice_number': sale.invoice_number,
            'date': sale.sale_date.strftime('%d/%m/%Y'),
            'total': sale.total_amount,
            'paid': sale.paid_amount,
            'status': sale.payment_status
        } for sale in recent_sales]
    })

@customers_bp.route('/delete/<int:id>', methods=['POST'])
@require_permission('manage_customers')
def delete_ajax(id):
    """Supprimer un client via modal"""
    try:
        data = request.get_json()
        reason = data.get('reason', '')
        
        customer = Customer.query.get_or_404(id)
        
        # Vérifier si le client a des ventes
        sales_count = Sale.query.filter_by(customer_id=customer.id).count()
        if sales_count > 0:
            # Désactiver au lieu de supprimer
            customer.is_active = False
        else:
            db.session.delete(customer)
        
        # Audit
        audit = Audit(
            user_id=current_user.id,
            action='delete_customer',
            entity_type='customer',
            entity_id=customer.id,
            details=f'Client supprimé: {customer.name}. Raison: {reason}',
            ip_address=request.remote_addr
        )
        db.session.add(audit)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Client supprimé avec succès' if sales_count == 0 else 'Client désactivé (avait des ventes)'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@customers_bp.route('/')
@require_permission('manage_customers')
def index():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    pharmacy_filter = request.args.get('pharmacy_id', 'all')
    type_filter = request.args.get('type', '')
    
    query = Customer.query
    
    # Filtrage par pharmacie
    query = filter_by_pharmacy(query, Customer, pharmacy_filter)
    
    if search:
        query = query.filter(
            db.or_(
                Customer.name.ilike(f'%{search}%'),
                Customer.email.ilike(f'%{search}%'),
                Customer.phone.ilike(f'%{search}%')
            )
        )
    
    if type_filter:
        query = query.filter(Customer.customer_type == type_filter)
    
    customers = query.order_by(Customer.created_at.desc()).paginate(
        page=page, per_page=6, error_out=False
    )
    
    pharmacies = get_accessible_pharmacies() if is_admin() else []
    
    return render_template('customers/index.html', 
                         customers=customers, 
                         search=search,
                         pharmacies=pharmacies,
                         pharmacy_filter=pharmacy_filter,
                         type_filter=type_filter)

@customers_bp.route('/export/<format>')
@require_permission('manage_customers')
def export(format):
    pharmacy_filter = request.args.get('pharmacy_id', 'all')
    search = request.args.get('search', '')
    
    query = Customer.query
    query = filter_by_pharmacy(query, Customer, pharmacy_filter)
    
    if search:
        query = query.filter(
            db.or_(
                Customer.name.ilike(f'%{search}%'),
                Customer.email.ilike(f'%{search}%'),
                Customer.phone.ilike(f'%{search}%')
            )
        )
    
    customers = query.order_by(Customer.name).all()
    
    headers = ['ID', 'Nom', 'Email', 'Téléphone', 'Type', 'Limite Crédit', 'Adresse', 'Pharmacie']
    
    data = []
    for c in customers:
        data.append({
            'ID': c.id,
            'Nom': c.name,
            'Email': c.email or '',
            'Téléphone': c.phone or '',
            'Type': c.customer_type,
            'Limite Crédit': c.credit_limit,
            'Adresse': c.address or '',
            'Pharmacie': c.pharmacy.name if c.pharmacy else 'N/A'
        })
    
    if format == 'csv':
        return export_to_csv(data, 'clients', headers)
    else:
        return export_to_excel(data, 'clients', headers, 'Clients')

@customers_bp.route('/quick-add', methods=['POST'])
@login_required
def quick_add():
    """Ajout rapide de client via modal (depuis POS)"""
    try:
        data = request.get_json()
        
        name = data.get('name')
        phone = data.get('phone')
        email = data.get('email')
        
        if not name:
            return jsonify({'success': False, 'message': 'Le nom est requis'}), 400
        
        customer = Customer(
            name=name,
            phone=phone,
            email=email,
            is_active=True
        )
        
        db.session.add(customer)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Client ajouté avec succès',
            'customer': {
                'id': customer.id,
                'name': customer.name,
                'phone': customer.phone,
                'email': customer.email
            }
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@customers_bp.route('/add', methods=['GET', 'POST'])
@require_permission('manage_customers')
def add():
    if request.method == 'POST':
        try:
            customer = Customer(
                name=request.form.get('name'),
                email=request.form.get('email'),
                phone=request.form.get('phone'),
                address=request.form.get('address'),
                customer_type=request.form.get('customer_type', 'regular'),
                credit_limit=float(request.form.get('credit_limit', 0))
            )
            
            db.session.add(customer)
            db.session.flush()
            
            audit = Audit(
                user_id=current_user.id,
                action='create_customer',
                entity_type='customer',
                entity_id=customer.id,
                details=f'Client créé: {customer.name}',
                ip_address=request.remote_addr
            )
            db.session.add(audit)
            
            db.session.commit()
            
            flash('Client ajouté avec succès!', 'success')
            return redirect(url_for('customers.index'))
        except Exception as e:
            db.session.rollback()
            flash(f'Erreur: {str(e)}', 'danger')
    
    return render_template('customers/add.html')

@customers_bp.route('/edit/<int:id>', methods=['GET', 'POST'])
@require_permission('manage_customers')
def edit(id):
    customer = Customer.query.get_or_404(id)
    
    if request.method == 'POST':
        try:
            customer.name = request.form.get('name')
            customer.email = request.form.get('email')
            customer.phone = request.form.get('phone')
            customer.address = request.form.get('address')
            customer.customer_type = request.form.get('customer_type', 'regular')
            customer.credit_limit = float(request.form.get('credit_limit', 0))
            
            audit = Audit(
                user_id=current_user.id,
                action='update_customer',
                entity_type='customer',
                entity_id=customer.id,
                details=f'Client modifié: {customer.name}',
                ip_address=request.remote_addr
            )
            db.session.add(audit)
            
            db.session.commit()
            
            flash('Client modifié avec succès!', 'success')
            return redirect(url_for('customers.index'))
        except Exception as e:
            db.session.rollback()
            flash(f'Erreur: {str(e)}', 'danger')
    
    return render_template('customers/edit.html', customer=customer)

@customers_bp.route('/view/<int:id>')
@require_permission('manage_customers')
def view(id):
    customer = Customer.query.get_or_404(id)
    sales = Sale.query.filter_by(customer_id=id).order_by(Sale.sale_date.desc()).all()
    payments = Payment.query.filter_by(customer_id=id).order_by(Payment.payment_date.desc()).all()
    
    return render_template('customers/view.html', customer=customer, sales=sales, payments=payments)

@customers_bp.route('/delete/<int:id>', methods=['POST'])
@require_permission('manage_customers')
def delete(id):
    customer = Customer.query.get_or_404(id)
    
    try:
        customer.is_active = False
        
        audit = Audit(
            user_id=current_user.id,
            action='delete_customer',
            entity_type='customer',
            entity_id=customer.id,
            details=f'Client supprimé: {customer.name}',
            ip_address=request.remote_addr
        )
        db.session.add(audit)
        
        db.session.commit()
        flash('Client supprimé avec succès!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erreur: {str(e)}', 'danger')
    
    return redirect(url_for('customers.index'))

@customers_bp.route('/toggle-status/<int:id>', methods=['POST'])
@require_permission('manage_customers')
def toggle_status(id):
    customer = Customer.query.get_or_404(id)
    customer.is_active = not customer.is_active
    
    audit = Audit(
        user_id=current_user.id,
        action='toggle_customer_status',
        entity_type='customer',
        entity_id=customer.id,
        details=f'Statut client changé: {customer.name} -> {"Actif" if customer.is_active else "Inactif"}',
        ip_address=request.remote_addr
    )
    db.session.add(audit)
    
    db.session.commit()
    
    flash(f'Client {"activé" if customer.is_active else "désactivé"} avec succès!', 'success')
    return redirect(url_for('customers.index'))

@customers_bp.route('/export-single/<int:id>')
@require_permission('manage_customers')
def export_single(id):
    customer = Customer.query.get_or_404(id)
    
    # Données à exporter
    export_data = {
        'customer': {
            'name': customer.name,
            'customer_type': customer.customer_type,
            'email': customer.email,
            'phone': customer.phone,
            'address': customer.address,
            'is_active': customer.is_active,
            'created_at': customer.created_at.isoformat() if customer.created_at else None
        },
        'sales': [],
        'total_purchases': 0
    }
    
    # Ventes du client
    sales = Sale.query.filter_by(customer_id=id).all()
    total_purchases = 0
    for sale in sales:
        export_data['sales'].append({
            'invoice_number': sale.invoice_number,
            'sale_date': sale.sale_date.isoformat() if sale.sale_date else None,
            'total_amount': sale.total_amount,
            'payment_status': sale.payment_status
        })
        total_purchases += sale.total_amount
    
    export_data['total_purchases'] = total_purchases
    
    # Créer un fichier JSON
    import json
    from flask import make_response
    
    response = make_response(json.dumps(export_data, indent=2, ensure_ascii=False))
    response.headers['Content-Type'] = 'application/json'
    response.headers['Content-Disposition'] = f'attachment; filename=customer_{customer.name}_export.json'
    
    return response

@customers_bp.route('/sales-history/<int:id>')
@require_permission('manage_customers')
def sales_history(id):
    """Historique des ventes d'un client"""
    customer = Customer.query.get_or_404(id)
    page = request.args.get('page', 1, type=int)
    
    sales = Sale.query.filter_by(customer_id=id).order_by(Sale.sale_date.desc()).paginate(
        page=page, per_page=10, error_out=False
    )
    
    return render_template('customers/sales_history.html', customer=customer, sales=sales)

@customers_bp.route('/payments-history/<int:id>')
@require_permission('manage_customers')
def payments_history(id):
    """Historique des paiements d'un client"""
    customer = Customer.query.get_or_404(id)
    page = request.args.get('page', 1, type=int)
    
    payments = Payment.query.filter_by(customer_id=id).order_by(Payment.payment_date.desc()).paginate(
        page=page, per_page=10, error_out=False
    )
    
    return render_template('customers/payments_history.html', customer=customer, payments=payments)

@customers_bp.route('/manage-credit/<int:id>', methods=['GET', 'POST'])
@require_permission('manage_customers')
def manage_credit(id):
    """Gérer le crédit d'un client"""
    customer = Customer.query.get_or_404(id)
    
    if request.method == 'POST':
        try:
            action = request.form.get('action')
            amount = float(request.form.get('amount', 0))
            notes = request.form.get('notes', '')
            
            if action == 'increase':
                customer.credit_limit += amount
                flash(f'Limite de crédit augmentée de ${amount:.2f}', 'success')
            elif action == 'decrease':
                customer.credit_limit = max(0, customer.credit_limit - amount)
                flash(f'Limite de crédit réduite de ${amount:.2f}', 'success')
            elif action == 'set':
                customer.credit_limit = amount
                flash(f'Limite de crédit définie à ${amount:.2f}', 'success')
            
            # Audit
            audit = Audit(
                user_id=current_user.id,
                action='manage_customer_credit',
                entity_type='customer',
                entity_id=customer.id,
                details=f'Crédit modifié: {action} ${amount}. Notes: {notes}',
                ip_address=request.remote_addr
            )
            db.session.add(audit)
            
            db.session.commit()
            return redirect(url_for('customers.manage_credit', id=id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Erreur: {str(e)}', 'danger')
    
    return render_template('customers/manage_credit.html', customer=customer)

@customers_bp.route('/change-type/<int:id>', methods=['GET', 'POST'])
@require_permission('manage_customers')
def change_type(id):
    """Changer le type d'un client"""
    customer = Customer.query.get_or_404(id)
    
    if request.method == 'POST':
        try:
            old_type = customer.customer_type
            customer.customer_type = request.form.get('customer_type', 'regular')
            
            # Audit
            audit = Audit(
                user_id=current_user.id,
                action='change_customer_type',
                entity_type='customer',
                entity_id=customer.id,
                details=f'Type changé: {old_type} -> {customer.customer_type}',
                ip_address=request.remote_addr
            )
            db.session.add(audit)
            
            db.session.commit()
            flash(f'Type de client changé en {customer.customer_type}', 'success')
            return redirect(url_for('customers.index'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Erreur: {str(e)}', 'danger')
    
    return render_template('customers/change_type.html', customer=customer)
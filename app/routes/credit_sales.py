from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from app.models import db, Sale, SalePayment, Customer, Pharmacy, User, Audit
from app.decorators import require_permission
from datetime import datetime
from sqlalchemy import func
from app.pharmacy_utils import filter_by_pharmacy, get_accessible_pharmacies, is_admin
from app.export_utils import export_to_csv, export_to_excel

credit_sales_bp = Blueprint('credit_sales', __name__, url_prefix='/credit-sales')

@credit_sales_bp.route('/')
@require_permission('manage_sales')
def index():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    filter_status = request.args.get('status', '')
    
    query = Sale.query.filter(Sale.payment_type == 'credit')
    
    if search:
        query = query.filter(
            db.or_(
                Sale.invoice_number.ilike(f'%{search}%'),
                Customer.name.ilike(f'%{search}%')
            )
        ).join(Customer, Sale.customer_id == Customer.id, isouter=True)
    
    if filter_status:
        query = query.filter(Sale.credit_status == filter_status)
    
    credit_sales = query.order_by(Sale.sale_date.desc()).paginate(
        page=page, per_page=6, error_out=False
    )
    
    stats = {
        'total_credit': Sale.query.filter_by(payment_type='credit').count(),
        'unpaid': Sale.query.filter_by(payment_type='credit', credit_status='unpaid').count(),
        'partially_paid': Sale.query.filter_by(payment_type='credit', credit_status='partially_paid').count(),
        'paid': Sale.query.filter_by(payment_type='credit', credit_status='paid').count(),
        'total_remaining': db.session.query(func.sum(Sale.remaining_amount)).filter_by(payment_type='credit').scalar() or 0
    }
    
    return render_template('credit_sales/index.html', 
                         credit_sales=credit_sales, 
                         stats=stats,
                         search=search,
                         filter_status=filter_status)

@credit_sales_bp.route('/show/<int:id>')
@require_permission('manage_sales')
def show(id):
    sale = Sale.query.filter_by(id=id, payment_type='credit').first_or_404()
    
    payment_history = SalePayment.query.filter_by(sale_id=id).order_by(SalePayment.payment_date.desc()).all()
    
    return render_template('credit_sales/show.html', sale=sale, payment_history=payment_history)

@credit_sales_bp.route('/add-payment/<int:sale_id>', methods=['POST'])
@require_permission('manage_payments')
def add_payment(sale_id):
    sale = Sale.query.filter_by(id=sale_id, payment_type='credit').first_or_404()
    
    try:
        data = request.get_json() if request.is_json else request.form
        
        amount = float(data.get('amount', 0))
        payment_method = data.get('payment_method', 'cash')
        reference = data.get('reference', f'PAY-{datetime.now().strftime("%Y%m%d%H%M%S")}')
        notes = data.get('notes', '')
        
        if amount <= 0:
            if request.is_json:
                return jsonify({'success': False, 'message': 'Montant invalide'}), 400
            flash('Montant invalide', 'danger')
            return redirect(url_for('credit_sales.show', id=sale_id))
        
        sale.calculate_remaining()
        
        if amount > sale.remaining_amount:
            if request.is_json:
                return jsonify({'success': False, 'message': 'Montant supérieur au solde restant'}), 400
            flash(f'Montant supérieur au solde restant ({sale.remaining_amount:.2f} $)', 'danger')
            return redirect(url_for('credit_sales.show', id=sale_id))
        
        sale_payment = SalePayment(
            sale_id=sale.id,
            amount=amount,
            payment_method=payment_method,
            reference=reference,
            notes=notes,
            created_by=current_user.id,
            status='confirmed'
        )
        
        db.session.add(sale_payment)
        
        sale.calculate_remaining()
        sale.update_credit_status()
        
        audit = Audit(
            user_id=current_user.id,
            action='add_credit_payment',
            entity_type='sale_payment',
            entity_id=sale_payment.id,
            details=f'Paiement partiel de {amount}$ pour vente {sale.invoice_number}',
            ip_address=request.remote_addr
        )
        db.session.add(audit)
        
        db.session.commit()
        
        if request.is_json:
            return jsonify({
                'success': True, 
                'remaining': sale.remaining_amount,
                'credit_status': sale.credit_status
            })
        
        flash(f'Paiement de {amount}$ enregistré avec succès!', 'success')
        return redirect(url_for('credit_sales.show', id=sale_id))
        
    except Exception as e:
        db.session.rollback()
        if request.is_json:
            return jsonify({'success': False, 'message': str(e)}), 500
        flash(f'Erreur: {str(e)}', 'danger')
        return redirect(url_for('credit_sales.show', id=sale_id))

@credit_sales_bp.route('/stats')
@require_permission('view_reports')
def stats():
    credit_sales = Sale.query.filter_by(payment_type='credit').all()
    
    customer_stats = {}
    for sale in credit_sales:
        if sale.customer:
            customer_id = sale.customer.id
            if customer_id not in customer_stats:
                customer_stats[customer_id] = {
                    'customer': sale.customer,
                    'total_credit': 0,
                    'total_paid': 0,
                    'total_remaining': 0,
                    'sales_count': 0
                }
            
            customer_stats[customer_id]['total_credit'] += sale.total_amount
            customer_stats[customer_id]['total_paid'] += (sale.total_amount - sale.remaining_amount)
            customer_stats[customer_id]['total_remaining'] += sale.remaining_amount
            customer_stats[customer_id]['sales_count'] += 1
    
    customer_list = sorted(customer_stats.values(), key=lambda x: x['total_remaining'], reverse=True)
    
    return render_template('credit_sales/stats.html', customer_stats=customer_list)


from flask import Blueprint, render_template, request, flash, redirect, url_for
from app.decorators import require_permission
from flask_login import login_required, current_user
from app.models import db, CashTransaction, Sale, Payment, Audit
from datetime import datetime
from sqlalchemy import func
from app.pharmacy_utils import filter_by_pharmacy, get_accessible_pharmacies, is_admin
from app.export_utils import export_to_csv, export_to_excel

cashier_bp = Blueprint('cashier', __name__, url_prefix='/cashier')

@cashier_bp.route('/')
@require_permission('manage_cashier')
def index():
    today = datetime.now().date()
    
    cash_in = db.session.query(func.sum(CashTransaction.amount)).filter(
        CashTransaction.transaction_type == 'in',
        func.date(CashTransaction.created_at) == today
    ).scalar() or 0
    
    cash_out = db.session.query(func.sum(CashTransaction.amount)).filter(
        CashTransaction.transaction_type == 'out',
        func.date(CashTransaction.created_at) == today
    ).scalar() or 0
    
    sales_cash = db.session.query(func.sum(Payment.amount)).filter(
        Payment.payment_method == 'cash',
        func.date(Payment.payment_date) == today
    ).scalar() or 0
    
    balance = cash_in + sales_cash - cash_out
    
    recent_transactions = CashTransaction.query.order_by(
        CashTransaction.created_at.desc()
    ).limit(20).all()
    
    return render_template('cashier/index.html',
                         cash_in=cash_in,
                         cash_out=cash_out,
                         sales_cash=sales_cash,
                         balance=balance,
                         transactions=recent_transactions)

@cashier_bp.route('/add-transaction', methods=['GET', 'POST'])
@require_permission('manage_cashier')
def add_transaction():
    if request.method == 'POST':
        try:
            transaction = CashTransaction(
                transaction_type=request.form.get('transaction_type'),
                amount=float(request.form.get('amount')),
                description=request.form.get('description'),
                reference=request.form.get('reference'),
                created_by=current_user.id
            )
            
            db.session.add(transaction)
            
            audit = Audit(
                user_id=current_user.id,
                action='cash_transaction',
                entity_type='cash',
                details=f'Transaction caisse: {transaction.transaction_type}, {transaction.amount}',
                ip_address=request.remote_addr
            )
            db.session.add(audit)
            
            db.session.commit()
            
            flash('Transaction enregistrée avec succès!', 'success')
            return redirect(url_for('cashier.index'))
        except Exception as e:
            db.session.rollback()
            flash(f'Erreur: {str(e)}', 'danger')
    
    return render_template('cashier/add_transaction.html')

@cashier_bp.route('/history')
@require_permission('manage_cashier')
def history():
    page = request.args.get('page', 1, type=int)
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    
    query = CashTransaction.query
    
    if date_from:
        query = query.filter(CashTransaction.created_at >= datetime.strptime(date_from, '%Y-%m-%d'))
    if date_to:
        query = query.filter(CashTransaction.created_at <= datetime.strptime(date_to, '%Y-%m-%d'))
    
    transactions = query.order_by(CashTransaction.created_at.desc()).paginate(
        page=page, per_page=6, error_out=False
    )
    
    return render_template('cashier/history.html', transactions=transactions)

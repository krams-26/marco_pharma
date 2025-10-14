from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from app.models import db, Payment, Sale, Customer, Audit

payments_bp = Blueprint('payments', __name__, url_prefix='/payments')

@payments_bp.route('/')
@login_required
def index():
    page = request.args.get('page', 1, type=int)
    
    payments = Payment.query.order_by(Payment.payment_date.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    
    return render_template('payments/index.html', payments=payments)

@payments_bp.route('/pending')
@login_required
def pending():
    pending_sales = Sale.query.filter(
        Sale.payment_status.in_(['pending', 'partial'])
    ).order_by(Sale.sale_date.desc()).all()
    
    return render_template('payments/pending.html', sales=pending_sales)

@payments_bp.route('/record/<int:sale_id>', methods=['GET', 'POST'])
@login_required
def record(sale_id):
    sale = Sale.query.get_or_404(sale_id)
    
    if request.method == 'POST':
        try:
            amount = float(request.form.get('amount'))
            payment_method = request.form.get('payment_method')
            reference = request.form.get('reference')
            notes = request.form.get('notes')
            
            if amount > sale.balance_due:
                flash('Le montant ne peut pas dépasser le solde dû!', 'danger')
                return redirect(url_for('payments.record', sale_id=sale_id))
            
            payment = Payment(
                sale_id=sale.id,
                customer_id=sale.customer_id,
                amount=amount,
                payment_method=payment_method,
                reference=reference,
                notes=notes
            )
            
            sale.paid_amount += amount
            
            if sale.paid_amount >= sale.total_amount:
                sale.payment_status = 'paid'
            else:
                sale.payment_status = 'partial'
            
            db.session.add(payment)
            
            audit = Audit(
                user_id=current_user.id,
                action='record_payment',
                entity_type='payment',
                entity_id=payment.id,
                details=f'Paiement enregistré: {amount} pour {sale.invoice_number}',
                ip_address=request.remote_addr
            )
            db.session.add(audit)
            
            db.session.commit()
            
            flash('Paiement enregistré avec succès!', 'success')
            return redirect(url_for('payments.pending'))
        except Exception as e:
            db.session.rollback()
            flash(f'Erreur: {str(e)}', 'danger')
    
    return render_template('payments/record.html', sale=sale)

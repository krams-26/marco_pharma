from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from app.decorators import require_permission
from flask_login import login_required, current_user
from app.models import db, Payment, Sale, Customer, Audit, SalePayment
from app.pharmacy_utils import filter_by_pharmacy, get_accessible_pharmacies, is_admin
from app.export_utils import export_to_csv, export_to_excel

payments_bp = Blueprint('payments', __name__, url_prefix='/payments')

@payments_bp.route('/quick-record', methods=['POST'])
@login_required
def quick_record():
    """Enregistrer un paiement rapide via modal"""
    try:
        data = request.get_json()
        
        sale_id = data.get('sale_id')
        amount = float(data.get('amount', 0))
        payment_method = data.get('payment_method', 'cash')
        notes = data.get('notes', '')
        
        if not sale_id or amount <= 0:
            return jsonify({'success': False, 'message': 'Données invalides'}), 400
        
        sale = Sale.query.get_or_404(sale_id)
        
        if amount > sale.balance_due:
            return jsonify({'success': False, 'message': f'Montant trop élevé. Solde restant: ${sale.balance_due:.2f}'}), 400
        
        # Créer le paiement
        payment = SalePayment(
            sale_id=sale.id,
            amount=amount,
            payment_method=payment_method,
            notes=notes,
            created_by=current_user.id
        )
        db.session.add(payment)
        
        # Mettre à jour le statut de la vente
        sale.paid_amount += amount
        if sale.paid_amount >= sale.total_amount:
            sale.payment_status = 'paid'
        else:
            sale.payment_status = 'partial'
        
        # Audit
        audit = Audit(
            user_id=current_user.id,
            action='create_payment',
            entity_type='sale_payment',
            entity_id=payment.id,
            details=f'Paiement de ${amount:.2f} pour vente {sale.invoice_number}',
            ip_address=request.remote_addr
        )
        db.session.add(audit)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Paiement enregistré avec succès',
            'new_paid_amount': sale.paid_amount,
            'new_balance': sale.balance_due,
            'new_status': sale.payment_status
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@payments_bp.route('/')
@require_permission('manage_payments')
def index():
    page = request.args.get('page', 1, type=int)
    pharmacy_filter = request.args.get('pharmacy_id', 'all')
    
    query = Payment.query.join(Sale)
    query = filter_by_pharmacy(query, Sale, pharmacy_filter)
    
    payments = query.order_by(Payment.payment_date.desc()).paginate(
        page=page, per_page=6, error_out=False
    )
    
    pharmacies = get_accessible_pharmacies() if is_admin() else []
    return render_template('payments/index.html', payments=payments, pharmacies=pharmacies, pharmacy_filter=pharmacy_filter)

@payments_bp.route('/export/<format>')
@require_permission('manage_payments')
def export(format):
    pharmacy_filter = request.args.get('pharmacy_id', 'all')
    
    query = Payment.query.join(Sale)
    query = filter_by_pharmacy(query, Sale, pharmacy_filter)
    payments = query.order_by(Payment.payment_date.desc()).all()
    
    headers = ['Date', 'Facture', 'Client', 'Montant', 'Méthode', 'Référence', 'Pharmacie']
    data = []
    for p in payments:
        data.append({
            'Date': p.payment_date.strftime('%d/%m/%Y %H:%M'),
            'Facture': p.sale.invoice_number,
            'Client': p.customer.name if p.customer else 'Anonyme',
            'Montant': p.amount,
            'Méthode': p.payment_method,
            'Référence': p.reference or '',
            'Pharmacie': p.sale.pharmacy.name if p.sale.pharmacy else 'N/A'
        })
    
    if format == 'csv':
        return export_to_csv(data, 'paiements', headers)
    else:
        return export_to_excel(data, 'paiements', headers, 'Paiements')

@payments_bp.route('/pending')
@require_permission('manage_payments')
def pending():
    pending_sales = Sale.query.filter(
        Sale.payment_status.in_(['pending', 'partial'])
    ).order_by(Sale.sale_date.desc()).all()
    
    return render_template('payments/pending.html', sales=pending_sales)

@payments_bp.route('/record/<int:sale_id>', methods=['GET', 'POST'])
@require_permission('manage_payments')
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
            
            # Mettre à jour les montants
            sale.paid_amount += amount
            sale.remaining_amount = sale.total_amount - sale.paid_amount
            
            # Mettre à jour le statut
            if sale.paid_amount >= sale.total_amount:
                sale.payment_status = 'paid'
                sale.credit_status = 'paid'
                sale.remaining_amount = 0
            else:
                sale.payment_status = 'partial'
                sale.credit_status = 'partially_paid'
            
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
            
            # Message de succès avec nouveau solde
            if sale.payment_status == 'paid':
                flash(f'Paiement enregistré! Facture {sale.invoice_number} entièrement payée.', 'success')
            else:
                new_balance = sale.balance_due
                flash(f'Paiement partiel enregistré! Nouveau solde: ${new_balance:.2f}', 'success')
            
            return redirect(url_for('payments.pending'))
        except Exception as e:
            db.session.rollback()
            flash(f'Erreur: {str(e)}', 'danger')
    
    return render_template('payments/record.html', sale=sale)

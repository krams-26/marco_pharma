from flask import Blueprint, render_template, request, flash, redirect, url_for
from app.decorators import require_permission
from flask_login import login_required, current_user
from app.models import db, Customer, Sale, Payment, Audit

customers_bp = Blueprint('customers', __name__, url_prefix='/customers')

@customers_bp.route('/')
@require_permission('manage_customers')
def index():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    
    query = Customer.query
    
    if search:
        query = query.filter(
            db.or_(
                Customer.name.ilike(f'%{search}%'),
                Customer.email.ilike(f'%{search}%'),
                Customer.phone.ilike(f'%{search}%')
            )
        )
    
    customers = query.order_by(Customer.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    
    return render_template('customers/index.html', customers=customers, search=search)

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

from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_required, current_user
from app import db
from app.models import Supplier, Product
from app.decorators import require_permission
from datetime import datetime

suppliers_bp = Blueprint('suppliers', __name__, url_prefix='/suppliers')

@suppliers_bp.route('/')
@login_required
@require_permission('manage_suppliers')
def index():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    status_filter = request.args.get('status', 'all')
    
    query = Supplier.query
    
    if search:
        query = query.filter(
            db.or_(
                Supplier.name.ilike(f'%{search}%'),
                Supplier.code.ilike(f'%{search}%'),
                Supplier.contact_person.ilike(f'%{search}%'),
                Supplier.email.ilike(f'%{search}%')
            )
        )
    
    if status_filter != 'all':
        query = query.filter_by(status=status_filter)
    
    suppliers = query.order_by(Supplier.name.asc()).paginate(
        page=page, per_page=6, error_out=False
    )
    
    stats = {
        'total': Supplier.query.count(),
        'active': Supplier.query.filter_by(status='active').count(),
        'inactive': Supplier.query.filter_by(status='inactive').count()
    }
    
    return render_template('suppliers/index.html', suppliers=suppliers, stats=stats)

@suppliers_bp.route('/create', methods=['GET', 'POST'])
@login_required
@require_permission('manage_suppliers')
def create():
    if request.method == 'POST':
        try:
            name = request.form.get('name')
            code = request.form.get('code')
            contact_person = request.form.get('contact_person')
            email = request.form.get('email')
            phone = request.form.get('phone')
            phone2 = request.form.get('phone2')
            address = request.form.get('address')
            city = request.form.get('city')
            country = request.form.get('country')
            website = request.form.get('website')
            tax_id = request.form.get('tax_id')
            payment_terms = request.form.get('payment_terms')
            credit_limit = float(request.form.get('credit_limit', 0))
            notes = request.form.get('notes')
            
            if not name:
                flash('Le nom du fournisseur est requis', 'danger')
                return redirect(url_for('suppliers.create'))
            
            if code and Supplier.query.filter_by(code=code).first():
                flash('Ce code fournisseur existe déjà', 'danger')
                return redirect(url_for('suppliers.create'))
            
            supplier = Supplier(
                name=name,
                code=code,
                contact_person=contact_person,
                email=email,
                phone=phone,
                phone2=phone2,
                address=address,
                city=city,
                country=country,
                website=website,
                tax_id=tax_id,
                payment_terms=payment_terms,
                credit_limit=credit_limit,
                notes=notes,
                status='active'
            )
            
            db.session.add(supplier)
            db.session.commit()
            
            flash(f'Fournisseur "{name}" créé avec succès', 'success')
            return redirect(url_for('suppliers.show', id=supplier.id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Erreur: {str(e)}', 'danger')
            return redirect(url_for('suppliers.create'))
    
    return render_template('suppliers/create.html')

@suppliers_bp.route('/<int:id>')
@login_required
@require_permission('manage_suppliers')
def show(id):
    supplier = Supplier.query.get_or_404(id)
    products = Product.query.filter_by(supplier_id=id).all()
    
    return render_template('suppliers/show.html', supplier=supplier, products=products)

@suppliers_bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@require_permission('manage_suppliers')
def edit(id):
    supplier = Supplier.query.get_or_404(id)
    
    if request.method == 'POST':
        try:
            supplier.name = request.form.get('name')
            code = request.form.get('code')
            
            if code and code != supplier.code:
                if Supplier.query.filter_by(code=code).first():
                    flash('Ce code fournisseur existe déjà', 'danger')
                    return redirect(url_for('suppliers.edit', id=id))
                supplier.code = code
            
            supplier.contact_person = request.form.get('contact_person')
            supplier.email = request.form.get('email')
            supplier.phone = request.form.get('phone')
            supplier.phone2 = request.form.get('phone2')
            supplier.address = request.form.get('address')
            supplier.city = request.form.get('city')
            supplier.country = request.form.get('country')
            supplier.website = request.form.get('website')
            supplier.tax_id = request.form.get('tax_id')
            supplier.payment_terms = request.form.get('payment_terms')
            supplier.credit_limit = float(request.form.get('credit_limit', 0))
            supplier.status = request.form.get('status', 'active')
            supplier.notes = request.form.get('notes')
            
            db.session.commit()
            flash('Fournisseur mis à jour avec succès', 'success')
            return redirect(url_for('suppliers.show', id=supplier.id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Erreur: {str(e)}', 'danger')
    
    return render_template('suppliers/edit.html', supplier=supplier)

@suppliers_bp.route('/<int:id>/delete', methods=['POST'])
@login_required
@require_permission('manage_suppliers')
def delete(id):
    supplier = Supplier.query.get_or_404(id)
    
    products_count = Product.query.filter_by(supplier_id=id).count()
    if products_count > 0:
        flash(f'Impossible de supprimer ce fournisseur car {products_count} produit(s) y sont liés', 'danger')
        return redirect(url_for('suppliers.show', id=id))
    
    try:
        db.session.delete(supplier)
        db.session.commit()
        flash('Fournisseur supprimé avec succès', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erreur: {str(e)}', 'danger')
    
    return redirect(url_for('suppliers.index'))

@suppliers_bp.route('/<int:id>/toggle-status', methods=['POST'])
@login_required
@require_permission('manage_suppliers')
def toggle_status(id):
    supplier = Supplier.query.get_or_404(id)
    
    try:
        supplier.status = 'inactive' if supplier.status == 'active' else 'active'
        db.session.commit()
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': True, 'status': supplier.status})
        
        flash(f'Statut du fournisseur mis à jour: {supplier.status}', 'success')
        return redirect(url_for('suppliers.show', id=id))
        
    except Exception as e:
        db.session.rollback()
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'message': str(e)}), 400
        flash(f'Erreur: {str(e)}', 'danger')
        return redirect(url_for('suppliers.show', id=id))

@suppliers_bp.route('/search')
@login_required
def search():
    query = request.args.get('q', '')
    
    if not query:
        return jsonify({'suppliers': []})
    
    suppliers = Supplier.query.filter(
        db.and_(
            Supplier.is_active == True,
            Supplier.status == 'active',
            db.or_(
                Supplier.name.ilike(f'%{query}%'),
                Supplier.code.ilike(f'%{query}%')
            )
        )
    ).limit(10).all()
    
    results = [
        {
            'id': s.id,
            'name': s.name,
            'code': s.code,
            'contact_person': s.contact_person,
            'phone': s.phone
        }
        for s in suppliers
    ]
    
    return jsonify({'suppliers': results})


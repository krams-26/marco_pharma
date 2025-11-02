from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from app.models import db, Pharmacy, UserPharmacy, User, Product, Sale, Audit
from app.decorators import require_permission
from datetime import datetime
from sqlalchemy import func
from app.pharmacy_utils import filter_by_pharmacy, get_accessible_pharmacies, is_admin
from app.export_utils import export_to_csv, export_to_excel

pharmacies_bp = Blueprint('pharmacies', __name__, url_prefix='/pharmacies')

@pharmacies_bp.route('/')
@require_permission('manage_settings')
def index():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    filter_type = request.args.get('type', '')
    
    query = Pharmacy.query
    
    if search:
        query = query.filter(
            db.or_(
                Pharmacy.name.ilike(f'%{search}%'),
                Pharmacy.code.ilike(f'%{search}%'),
                Pharmacy.address.ilike(f'%{search}%')
            )
        )
    
    if filter_type:
        query = query.filter_by(type=filter_type)
    
    pharmacies = query.order_by(Pharmacy.created_at.desc()).paginate(
        page=page, per_page=6, error_out=False
    )
    
    stats = {
        'total': Pharmacy.query.filter_by(is_active=True).count(),
        'pharmacies': Pharmacy.query.filter_by(type='pharmacy', is_active=True).count(),
        'depots': Pharmacy.query.filter_by(type='depot', is_active=True).count(),
    }
    
    return render_template('pharmacies/index.html', pharmacies=pharmacies, search=search, filter_type=filter_type, stats=stats)

@pharmacies_bp.route('/create', methods=['GET', 'POST'])
@require_permission('manage_settings')
def create():
    if request.method == 'POST':
        try:
            pharmacy = Pharmacy(
                name=request.form.get('name'),
                type=request.form.get('type', 'pharmacy'),
                code=request.form.get('code'),
                address=request.form.get('address'),
                phone=request.form.get('phone'),
                email=request.form.get('email'),
                manager_name=request.form.get('manager_name'),
                license_number=request.form.get('license_number'),
                opening_hours=request.form.get('opening_hours'),
                revenue_target=float(request.form.get('revenue_target', 0)),
                status='active',
                is_active=True
            )
            
            db.session.add(pharmacy)
            db.session.flush()
            
            audit = Audit(
                user_id=current_user.id,
                action='create_pharmacy',
                entity_type='pharmacy',
                entity_id=pharmacy.id,
                details=f'Pharmacie créée: {pharmacy.name}',
                ip_address=request.remote_addr
            )
            db.session.add(audit)
            
            db.session.commit()
            
            flash('Pharmacie créée avec succès!', 'success')
            return redirect(url_for('pharmacies.index'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Erreur: {str(e)}', 'danger')
    
    return render_template('pharmacies/create.html')

@pharmacies_bp.route('/edit/<int:id>', methods=['GET', 'POST'])
@require_permission('manage_settings')
def edit(id):
    pharmacy = Pharmacy.query.get_or_404(id)
    
    if request.method == 'POST':
        try:
            pharmacy.name = request.form.get('name')
            pharmacy.type = request.form.get('type', 'pharmacy')
            pharmacy.code = request.form.get('code')
            pharmacy.address = request.form.get('address')
            pharmacy.phone = request.form.get('phone')
            pharmacy.email = request.form.get('email')
            pharmacy.manager_name = request.form.get('manager_name')
            pharmacy.license_number = request.form.get('license_number')
            pharmacy.opening_hours = request.form.get('opening_hours')
            
            pharmacy.revenue_target = float(request.form.get('revenue_target', 0))
            pharmacy.status = request.form.get('status', 'active')
            pharmacy.is_active = request.form.get('is_active') == 'on'
            
            audit = Audit(
                user_id=current_user.id,
                action='update_pharmacy',
                entity_type='pharmacy',
                entity_id=pharmacy.id,
                details=f'Pharmacie modifiée: {pharmacy.name}',
                ip_address=request.remote_addr
            )
            db.session.add(audit)
            
            db.session.commit()
            
            flash('Pharmacie modifiée avec succès!', 'success')
            return redirect(url_for('pharmacies.index'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Erreur: {str(e)}', 'danger')
    
    return render_template('pharmacies/edit.html', pharmacy=pharmacy)

@pharmacies_bp.route('/view/<int:id>')
@require_permission('manage_settings')
def view(id):
    pharmacy = Pharmacy.query.get_or_404(id)
    
    users = UserPharmacy.query.filter_by(pharmacy_id=id).all()
    
    products_count = Product.query.filter_by(pharmacy_id=id, is_active=True).count()
    sales_count = Sale.query.filter_by(pharmacy_id=id).count()
    
    total_sales = db.session.query(func.sum(Sale.total_amount)).filter_by(pharmacy_id=id).scalar() or 0
    
    stats = {
        'users_count': len(users),
        'products_count': products_count,
        'sales_count': sales_count,
        'total_revenue': total_sales
    }
    
    return render_template('pharmacies/view.html', pharmacy=pharmacy, users=users, stats=stats)

@pharmacies_bp.route('/delete/<int:id>', methods=['POST'])
@require_permission('manage_settings')
def delete(id):
    pharmacy = Pharmacy.query.get_or_404(id)
    
    try:
        products_count = Product.query.filter_by(pharmacy_id=id).count()
        sales_count = Sale.query.filter_by(pharmacy_id=id).count()
        
        if products_count > 0 or sales_count > 0:
            flash('Impossible de supprimer une pharmacie avec des produits ou des ventes associées. Désactivez-la plutôt.', 'danger')
            return redirect(url_for('pharmacies.index'))
        
        audit = Audit(
            user_id=current_user.id,
            action='delete_pharmacy',
            entity_type='pharmacy',
            entity_id=pharmacy.id,
            details=f'Pharmacie supprimée: {pharmacy.name}',
            ip_address=request.remote_addr
        )
        db.session.add(audit)
        
        db.session.delete(pharmacy)
        db.session.commit()
        
        flash('Pharmacie supprimée avec succès!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erreur: {str(e)}', 'danger')
    
    return redirect(url_for('pharmacies.index'))

@pharmacies_bp.route('/assign-user/<int:id>', methods=['GET', 'POST'])
@require_permission('manage_settings')
def assign_user(id):
    pharmacy = Pharmacy.query.get_or_404(id)
    
    if request.method == 'POST':
        try:
            user_id = request.form.get('user_id')
            is_primary = request.form.get('is_primary') == 'on'
            
            existing = UserPharmacy.query.filter_by(user_id=user_id, pharmacy_id=id).first()
            if existing:
                flash('Cet utilisateur est déjà affecté à cette pharmacie!', 'warning')
                return redirect(url_for('pharmacies.assign_user', id=id))
            
            if is_primary:
                UserPharmacy.query.filter_by(user_id=user_id, is_primary=True).update({'is_primary': False})
            
            assignment = UserPharmacy(
                user_id=user_id,
                pharmacy_id=id,
                is_primary=is_primary,
                assigned_by=current_user.id
            )
            
            db.session.add(assignment)
            
            audit = Audit(
                user_id=current_user.id,
                action='assign_user_pharmacy',
                entity_type='user_pharmacy',
                details=f'Utilisateur {user_id} affecté à pharmacie {pharmacy.name}',
                ip_address=request.remote_addr
            )
            db.session.add(audit)
            
            db.session.commit()
            
            flash('Utilisateur affecté avec succès!', 'success')
            return redirect(url_for('pharmacies.view', id=id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Erreur: {str(e)}', 'danger')
    
    assigned_user_ids = [ua.user_id for ua in UserPharmacy.query.filter_by(pharmacy_id=id).all()]
    available_users = User.query.filter(User.id.notin_(assigned_user_ids) if assigned_user_ids else True).filter_by(is_active=True).all()
    
    return render_template('pharmacies/assign_user.html', pharmacy=pharmacy, available_users=available_users)

@pharmacies_bp.route('/remove-user/<int:pharmacy_id>/<int:user_id>', methods=['POST'])
@require_permission('manage_settings')
def remove_user(pharmacy_id, user_id):
    assignment = UserPharmacy.query.filter_by(pharmacy_id=pharmacy_id, user_id=user_id).first_or_404()
    
    try:
        audit = Audit(
            user_id=current_user.id,
            action='remove_user_pharmacy',
            entity_type='user_pharmacy',
            details=f'Utilisateur {user_id} retiré de pharmacie {pharmacy_id}',
            ip_address=request.remote_addr
        )
        db.session.add(audit)
        
        db.session.delete(assignment)
        db.session.commit()
        
        flash('Utilisateur retiré de la pharmacie avec succès!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erreur: {str(e)}', 'danger')
    
    return redirect(url_for('pharmacies.view', id=pharmacy_id))

@pharmacies_bp.route('/stats')
@require_permission('view_reports')
def stats():
    pharmacies = Pharmacy.query.filter_by(is_active=True).all()
    
    pharmacy_stats = []
    for pharmacy in pharmacies:
        total_sales = db.session.query(func.sum(Sale.total_amount)).filter_by(pharmacy_id=pharmacy.id).scalar() or 0
        sales_count = Sale.query.filter_by(pharmacy_id=pharmacy.id).count()
        products_count = Product.query.filter_by(pharmacy_id=pharmacy.id, is_active=True).count()
        users_count = UserPharmacy.query.filter_by(pharmacy_id=pharmacy.id).count()
        
        pharmacy_stats.append({
            'pharmacy': pharmacy,
            'total_revenue': total_sales,
            'sales_count': sales_count,
            'products_count': products_count,
            'users_count': users_count,
            'target_progress': (total_sales / pharmacy.revenue_target * 100) if pharmacy.revenue_target > 0 else 0
        })
    
    pharmacy_stats.sort(key=lambda x: x['total_revenue'], reverse=True)
    
    return render_template('pharmacies/stats.html', pharmacy_stats=pharmacy_stats)

@pharmacies_bp.route('/toggle-status/<int:id>', methods=['POST'])
@require_permission('manage_settings')
def toggle_status(id):
    pharmacy = Pharmacy.query.get_or_404(id)
    pharmacy.is_active = not pharmacy.is_active
    pharmacy.status = 'active' if pharmacy.is_active else 'inactive'
    
    audit = Audit(
        user_id=current_user.id,
        action='toggle_pharmacy_status',
        entity_type='pharmacy',
        entity_id=pharmacy.id,
        details=f'Statut pharmacie changé: {pharmacy.name} -> {"Actif" if pharmacy.is_active else "Inactif"}',
        ip_address=request.remote_addr
    )
    db.session.add(audit)
    
    db.session.commit()
    
    flash(f'Pharmacie {"activée" if pharmacy.is_active else "désactivée"} avec succès!', 'success')
    return redirect(url_for('pharmacies.index'))

@pharmacies_bp.route('/export/<int:id>')
@require_permission('manage_settings')
def export(id):
    pharmacy = Pharmacy.query.get_or_404(id)
    
    # Données à exporter
    export_data = {
        'pharmacy': {
            'name': pharmacy.name,
            'type': pharmacy.type,
            'code': pharmacy.code,
            'address': pharmacy.address,
            'phone': pharmacy.phone,
            'email': pharmacy.email,
            'status': pharmacy.status,
            'manager_name': pharmacy.manager_name,
            'license_number': pharmacy.license_number,
            'opening_hours': pharmacy.opening_hours,
            'revenue_target': pharmacy.revenue_target,
            'is_active': pharmacy.is_active
        },
        'users': [],
        'products': [],
        'sales_summary': {}
    }
    
    # Utilisateurs affectés
    user_pharmacies = UserPharmacy.query.filter_by(pharmacy_id=id).all()
    for up in user_pharmacies:
        user = User.query.get(up.user_id)
        if user:
            export_data['users'].append({
                'username': user.username,
                'full_name': user.full_name,
                'email': user.email,
                'role': user.role,
                'is_primary': up.is_primary
            })
    
    # Produits
    products = Product.query.filter_by(pharmacy_id=id, is_active=True).all()
    for product in products:
        export_data['products'].append({
            'name': product.name,
            'barcode': product.barcode,
            'category': product.category,
            'selling_price': product.selling_price,
            'stock_quantity': product.stock_quantity
        })
    
    # Résumé des ventes
    total_sales = db.session.query(func.sum(Sale.total_amount)).filter_by(pharmacy_id=id).scalar() or 0
    sales_count = Sale.query.filter_by(pharmacy_id=id).count()
    export_data['sales_summary'] = {
        'total_revenue': total_sales,
        'sales_count': sales_count
    }
    
    # Créer un fichier JSON
    import json
    from flask import make_response
    
    response = make_response(json.dumps(export_data, indent=2, ensure_ascii=False))
    response.headers['Content-Type'] = 'application/json'
    response.headers['Content-Disposition'] = f'attachment; filename=pharmacy_{pharmacy.code}_export.json'
    
    return response


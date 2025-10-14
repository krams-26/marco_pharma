from flask import Blueprint, render_template, request, flash, redirect, url_for
from app.decorators import require_permission
from flask_login import login_required, current_user
from app.models import db, User, Audit

users_bp = Blueprint('users', __name__, url_prefix='/users')

PERMISSIONS = [
    ('view_dashboard', 'Voir le tableau de bord'),
    ('manage_products', 'Gérer les produits'),
    ('manage_sales', 'Gérer les ventes'),
    ('manage_customers', 'Gérer les clients'),
    ('manage_users', 'Gérer les utilisateurs'),
    ('manage_stock', 'Gérer le stock'),
    ('manage_hr', 'Gérer le personnel'),
    ('manage_payments', 'Gérer les paiements'),
    ('manage_cashier', 'Gérer la caisse'),
    ('view_reports', 'Voir les rapports'),
    ('view_audits', 'Voir les audits'),
    ('manage_settings', 'Gérer les paramètres'),
]

ROLES = [
    ('admin', 'Administrateur'),
    ('manager', 'Manager'),
    ('pharmacien', 'Pharmacien'),
    ('caissier', 'Caissier'),
    ('vendeur', 'Vendeur'),
]

@users_bp.route('/')
@require_permission('manage_users')
def index():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    
    query = User.query
    
    if search:
        query = query.filter(
            db.or_(
                User.username.ilike(f'%{search}%'),
                User.email.ilike(f'%{search}%'),
                User.first_name.ilike(f'%{search}%'),
                User.last_name.ilike(f'%{search}%')
            )
        )
    
    users = query.order_by(User.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    
    return render_template('users/index.html', users=users, search=search)

@users_bp.route('/add', methods=['GET', 'POST'])
@require_permission('manage_users')
def add():
    if request.method == 'POST':
        try:
            user = User(
                username=request.form.get('username'),
                email=request.form.get('email'),
                first_name=request.form.get('first_name'),
                last_name=request.form.get('last_name'),
                phone=request.form.get('phone'),
                role=request.form.get('role', 'vendeur'),
                is_active=request.form.get('is_active') == 'on'
            )
            
            user.set_password(request.form.get('password'))
            
            perms = {}
            for perm, _ in PERMISSIONS:
                perms[perm] = request.form.get(f'perm_{perm}') == 'on'
            user.set_permissions(perms)
            
            db.session.add(user)
            db.session.flush()
            
            audit = Audit(
                user_id=current_user.id,
                action='create_user',
                entity_type='user',
                entity_id=user.id,
                details=f'Utilisateur créé: {user.username}',
                ip_address=request.remote_addr
            )
            db.session.add(audit)
            
            db.session.commit()
            
            flash('Utilisateur ajouté avec succès!', 'success')
            return redirect(url_for('users.index'))
        except Exception as e:
            db.session.rollback()
            flash(f'Erreur: {str(e)}', 'danger')
    
    return render_template('users/add.html', permissions=PERMISSIONS, roles=ROLES)

@users_bp.route('/edit/<int:id>', methods=['GET', 'POST'])
@require_permission('manage_users')
def edit(id):
    user = User.query.get_or_404(id)
    
    if request.method == 'POST':
        try:
            user.username = request.form.get('username')
            user.email = request.form.get('email')
            user.first_name = request.form.get('first_name')
            user.last_name = request.form.get('last_name')
            user.phone = request.form.get('phone')
            user.role = request.form.get('role', 'vendeur')
            user.is_active = request.form.get('is_active') == 'on'
            
            password = request.form.get('password')
            if password:
                user.set_password(password)
            
            perms = {}
            for perm, _ in PERMISSIONS:
                perms[perm] = request.form.get(f'perm_{perm}') == 'on'
            user.set_permissions(perms)
            
            audit = Audit(
                user_id=current_user.id,
                action='update_user',
                entity_type='user',
                entity_id=user.id,
                details=f'Utilisateur modifié: {user.username}',
                ip_address=request.remote_addr
            )
            db.session.add(audit)
            
            db.session.commit()
            
            flash('Utilisateur modifié avec succès!', 'success')
            return redirect(url_for('users.index'))
        except Exception as e:
            db.session.rollback()
            flash(f'Erreur: {str(e)}', 'danger')
    
    return render_template('users/edit.html', user=user, permissions=PERMISSIONS, roles=ROLES)

@users_bp.route('/delete/<int:id>', methods=['POST'])
@require_permission('manage_users')
def delete(id):
    if id == current_user.id:
        flash('Vous ne pouvez pas supprimer votre propre compte!', 'danger')
        return redirect(url_for('users.index'))
    
    user = User.query.get_or_404(id)
    
    try:
        user.is_active = False
        
        audit = Audit(
            user_id=current_user.id,
            action='delete_user',
            entity_type='user',
            entity_id=user.id,
            details=f'Utilisateur supprimé: {user.username}',
            ip_address=request.remote_addr
        )
        db.session.add(audit)
        
        db.session.commit()
        flash('Utilisateur supprimé avec succès!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erreur: {str(e)}', 'danger')
    
    return redirect(url_for('users.index'))

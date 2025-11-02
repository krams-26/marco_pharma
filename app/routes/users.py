from flask import Blueprint, render_template, request, flash, redirect, url_for
from app.decorators import require_permission
from flask_login import login_required, current_user
from app.models import db, User, Audit, Pharmacy, UserPharmacy, Employee
from app.pharmacy_utils import filter_by_pharmacy, get_accessible_pharmacies, is_admin
from app.export_utils import export_to_csv, export_to_excel
from datetime import datetime, date

users_bp = Blueprint('users', __name__, url_prefix='/users')

PERMISSIONS_BY_MODULE = {
    'Dashboard': [
    ('view_dashboard', 'Voir le tableau de bord'),
        ('dashboard_stats', 'Voir les statistiques'),
    ],
    'Produits': [
        ('products_view', 'Voir les produits'),
        ('products_create', 'Créer un produit'),
        ('products_edit', 'Modifier un produit'),
        ('products_delete', 'Supprimer un produit'),
        ('products_import', 'Importer des produits'),
        ('products_export', 'Exporter des produits'),
        ('products_alerts', 'Voir les alertes stock'),
    ],
    'Stock': [
        ('stock_view', 'Voir le stock'),
        ('stock_movements', 'Voir les mouvements'),
        ('stock_adjust', 'Ajuster le stock'),
        ('stock_transfer', 'Transférer entre pharmacies'),
        ('stock_inventory', 'Faire un inventaire'),
        ('stock_lots', 'Gérer les lots'),
        ('stock_alerts', 'Voir les alertes'),
    ],
    'Ventes': [
        ('sales_view', 'Voir les ventes'),
        ('sales_create', 'Créer une vente'),
        ('sales_edit', 'Modifier une vente'),
        ('sales_delete', 'Supprimer une vente'),
        ('sales_cancel', 'Annuler une vente'),
        ('sales_validate', 'Valider une vente'),
        ('sales_print', 'Imprimer une facture'),
        ('sales_export', 'Exporter les ventes'),
        ('sales_discount', 'Appliquer une remise'),
    ],
    'Point de Vente (POS)': [
        ('pos_access', 'Accès au point de vente'),
        ('pos_create_sale', 'Créer une vente'),
        ('pos_hold_sale', 'Mettre en attente'),
        ('pos_recall_sale', 'Reprendre une vente'),
    ],
    'Clients': [
        ('customers_view', 'Voir les clients'),
        ('customers_create', 'Créer un client'),
        ('customers_edit', 'Modifier un client'),
        ('customers_delete', 'Supprimer un client'),
        ('customers_export', 'Exporter les clients'),
    ],
    'Fournisseurs': [
        ('suppliers_view', 'Voir les fournisseurs'),
        ('suppliers_create', 'Créer un fournisseur'),
        ('suppliers_edit', 'Modifier un fournisseur'),
        ('suppliers_delete', 'Supprimer un fournisseur'),
    ],
    'Caisse': [
        ('cashier_access', 'Accès à la caisse'),
        ('cashier_open', 'Ouvrir une session'),
        ('cashier_close', 'Fermer une session'),
        ('cashier_view_history', 'Voir l\'historique'),
    ],
    'Paiements': [
        ('payments_view', 'Voir les paiements'),
        ('payments_create', 'Enregistrer un paiement'),
        ('payments_edit', 'Modifier un paiement'),
        ('payments_delete', 'Supprimer un paiement'),
        ('payments_pending', 'Voir les paiements en attente'),
    ],
    'Proforma': [
        ('proforma_view', 'Voir les proformas'),
        ('proforma_create', 'Créer une proforma'),
        ('proforma_edit', 'Modifier une proforma'),
        ('proforma_delete', 'Supprimer une proforma'),
        ('proforma_convert', 'Convertir en vente'),
        ('proforma_print', 'Imprimer une proforma'),
    ],
    'Ventes à Crédit': [
        ('credit_sales_view', 'Voir les ventes à crédit'),
        ('credit_sales_add_payment', 'Ajouter un paiement'),
        ('credit_sales_stats', 'Voir les statistiques'),
    ],
    'Personnel (RH)': [
        ('hr_view', 'Voir le personnel'),
        ('hr_create', 'Créer un employé'),
        ('hr_edit', 'Modifier un employé'),
        ('hr_delete', 'Supprimer un employé'),
        ('hr_salaries', 'Gérer les salaires'),
        ('hr_pay_salary', 'Payer un salaire'),
        ('hr_leaves', 'Gérer les congés'),
        ('hr_absences', 'Gérer les absences'),
        ('hr_credits', 'Gérer les avances'),
    ],
    'Évaluation Personnel': [
        ('evaluations_view', 'Voir les évaluations'),
        ('evaluations_create', 'Créer une évaluation'),
        ('evaluations_edit', 'Modifier une évaluation'),
        ('evaluations_delete', 'Supprimer une évaluation'),
    ],
    'Tâches': [
        ('tasks_view', 'Voir les tâches'),
        ('tasks_create', 'Créer une tâche'),
        ('tasks_edit', 'Modifier une tâche'),
        ('tasks_delete', 'Supprimer une tâche'),
        ('tasks_assign', 'Assigner une tâche'),
        ('tasks_complete', 'Marquer comme complète'),
    ],
    'Approbations': [
        ('approvals_view', 'Voir les approbations'),
        ('approvals_create', 'Créer une demande'),
        ('approvals_approve', 'Approuver une demande'),
        ('approvals_reject', 'Rejeter une demande'),
        ('approvals_delete', 'Supprimer une demande'),
    ],
    'Pharmacies': [
        ('pharmacies_view', 'Voir les pharmacies'),
        ('pharmacies_create', 'Créer une pharmacie'),
        ('pharmacies_edit', 'Modifier une pharmacie'),
        ('pharmacies_delete', 'Supprimer une pharmacie'),
        ('pharmacies_assign_users', 'Assigner des utilisateurs'),
        ('pharmacies_stats', 'Voir les statistiques'),
    ],
    'Utilisateurs': [
        ('users_view', 'Voir les utilisateurs'),
        ('users_create', 'Créer un utilisateur'),
        ('users_edit', 'Modifier un utilisateur'),
        ('users_delete', 'Supprimer un utilisateur'),
        ('users_permissions', 'Gérer les permissions'),
        ('users_export', 'Exporter les utilisateurs'),
    ],
    'Rapports': [
        ('reports_view', 'Voir les rapports'),
        ('reports_sales', 'Rapport des ventes'),
        ('reports_stock', 'Rapport de stock'),
        ('reports_products', 'Rapport des produits'),
        ('reports_pharmacies', 'Rapport des pharmacies'),
        ('reports_export', 'Exporter les rapports'),
        ('reports_print', 'Imprimer les rapports'),
    ],
    'Notifications': [
        ('notifications_view', 'Voir les notifications'),
        ('notifications_create', 'Créer une notification'),
        ('notifications_mark_read', 'Marquer comme lu'),
    ],
    'Audit': [
        ('audits_view', 'Voir les audits'),
        ('audits_export', 'Exporter les audits'),
    ],
    'Paramètres': [
        ('settings_view', 'Voir les paramètres'),
        ('settings_edit', 'Modifier les paramètres'),
        ('settings_exchange_rates', 'Gérer les taux de change'),
        ('settings_company', 'Paramètres entreprise'),
        ('settings_system', 'Paramètres système'),
    ],
    'Codes de Validation': [
        ('validation_request', 'Demander un code'),
        ('validation_validate', 'Valider un code'),
        ('validation_view_codes', 'Voir les codes'),
    ],
    'Profil': [
        ('profile_view', 'Voir mon profil'),
        ('profile_edit', 'Modifier mon profil'),
    ],
}

# Liste plate pour compatibilité
PERMISSIONS = []
for module, perms in PERMISSIONS_BY_MODULE.items():
    PERMISSIONS.extend(perms)

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
        page=page, per_page=6, error_out=False
    )
    
    # Récupérer la pharmacie principale assignée à chaque utilisateur affiché
    user_ids = [u.id for u in users.items]
    user_primary_pharmacy = {}
    if user_ids:
        assignments = (
            db.session.query(UserPharmacy.user_id, Pharmacy.name, UserPharmacy.is_primary)
            .join(Pharmacy, UserPharmacy.pharmacy_id == Pharmacy.id)
            .filter(UserPharmacy.user_id.in_(user_ids))
            .order_by(UserPharmacy.is_primary.desc())
            .all()
        )
        # Garder la première (priorité à is_primary=True)
        for uid, pharmacy_name, is_primary in assignments:
            if uid not in user_primary_pharmacy:
                user_primary_pharmacy[uid] = pharmacy_name
    
    return render_template('users/index.html', users=users, search=search, user_primary_pharmacy=user_primary_pharmacy)

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
            
            # Ne mettre à jour les permissions que si des champs de permissions ont été envoyés
            has_perm_fields = any(k.startswith('perm_') for k in request.form.keys())
            if has_perm_fields:
                perms = {}
                for perm, _ in PERMISSIONS:
                    perms[perm] = request.form.get(f'perm_{perm}') == 'on'
                user.set_permissions(perms)
            
            db.session.add(user)
            db.session.flush()
            
            # Affectation de la pharmacie
            pharmacy_id = request.form.get('pharmacy_id')
            if pharmacy_id:
                user_pharmacy = UserPharmacy(
                    user_id=user.id,
                    pharmacy_id=int(pharmacy_id),
                    is_primary=True
                )
                db.session.add(user_pharmacy)
            
            # Créer automatiquement un employé pour cet utilisateur
            import random
            employee_id = f"EMP{date.today().strftime('%Y')}{random.randint(1000, 9999)}"
            employee = Employee(
                user_id=user.id,
                employee_id=employee_id,
                position=user.role.capitalize(),
                department='Général',
                salary=0.0,
                hire_date=date.today(),
                is_active=True
            )
            db.session.add(employee)
            
            audit = Audit(
                user_id=current_user.id,
                action='create_user',
                entity_type='user',
                entity_id=user.id,
                details=f'Utilisateur et employé créés: {user.username}',
                ip_address=request.remote_addr
            )
            db.session.add(audit)
            
            db.session.commit()
            
            flash('Utilisateur ajouté avec succès!', 'success')
            return redirect(url_for('users.index'))
        except Exception as e:
            db.session.rollback()
            flash(f'Erreur: {str(e)}', 'danger')
    
    pharmacies = Pharmacy.query.all()
    return render_template('users/add.html', permissions=PERMISSIONS, permissions_by_module=PERMISSIONS_BY_MODULE, roles=ROLES, pharmacies=pharmacies)

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
            
            # Mettre à jour les permissions: lire toutes les cases transmises
            perms = {}
            for perm, _ in PERMISSIONS:
                perms[perm] = request.form.get(f'perm_{perm}') == 'on'
            # Si aucune case n'est envoyée, conserver l'existant
            if any(perms.values()) or any(k.startswith('perm_') for k in request.form.keys()):
                user.set_permissions(perms)
            
            # Mettre à jour l'affectation de pharmacie
            db.session.query(UserPharmacy).filter_by(user_id=user.id).delete()
            
            pharmacy_id = request.form.get('pharmacy_id')
            if pharmacy_id:
                user_pharmacy = UserPharmacy(
                    user_id=user.id,
                    pharmacy_id=int(pharmacy_id),
                    is_primary=True
                )
                db.session.add(user_pharmacy)
            
            # Créer un employé s'il n'en a pas
            employee = Employee.query.filter_by(user_id=user.id).first()
            if not employee:
                import random
                employee_id = f"EMP{date.today().strftime('%Y')}{random.randint(1000, 9999)}"
                employee = Employee(
                    user_id=user.id,
                    employee_id=employee_id,
                    position=user.role.capitalize(),
                    department='Général',
                    salary=0.0,
                    hire_date=date.today(),
                    is_active=user.is_active
                )
                db.session.add(employee)
            else:
                # Mettre à jour le statut de l'employé
                employee.is_active = user.is_active
                employee.position = user.role.capitalize()
            
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
    
    pharmacies = Pharmacy.query.all()
    # Pré-remplir fin selon règles:
    # 1) Admin: tout vrai
    # 2) Si perm explicite dans JSON
    # 3) Si manage_* correspondant au préfixe du module est vrai (compat héritage)
    user_raw_perms = user.get_permissions() or {}
    prefill_permissions = {}
    if user.role == 'admin':
        for perm, _ in PERMISSIONS:
            prefill_permissions[perm] = True
    else:
        def has_manage(prefix):
            mapping = {
                'products_': 'manage_products',
                'sales_': 'manage_sales',
                'customers_': 'manage_customers',
                'users_': 'manage_users',
                'stock_': 'manage_stock',
                'hr_': 'manage_hr',
                'payments_': 'manage_payments',
                'cashier_': 'manage_cashier',
                'reports_': 'view_reports',
                'pharmacies_': 'manage_settings',
                'settings_': 'manage_settings',
                'approvals_': 'view_approvals',
                'tasks_': 'tasks_view',
                'proforma_': 'sales_view',
                'credit_sales_': 'sales_view',
            }
            key = mapping.get(prefix)
            return bool(user_raw_perms.get(key)) if key else False

        for perm, _ in PERMISSIONS:
            explicit = bool(user_raw_perms.get(perm))
            if explicit:
                prefill_permissions[perm] = True
                continue
            # Déterminer le préfixe
            prefix = None
            for p in ['products_','sales_','customers_','users_','stock_','hr_','payments_','cashier_','reports_','pharmacies_','settings_','approvals_','tasks_','proforma_','credit_sales_']:
                if perm.startswith(p):
                    prefix = p
                    break
            prefill_permissions[perm] = has_manage(prefix) if prefix else False
    return render_template(
        'users/edit.html',
        user=user,
        permissions=PERMISSIONS,
        permissions_by_module=PERMISSIONS_BY_MODULE,
        roles=ROLES,
        pharmacies=pharmacies,
        prefill_permissions=prefill_permissions,
    )

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

@users_bp.route('/view/<int:id>')
@require_permission('manage_users')
def view(id):
    """View user details"""
    user = User.query.get_or_404(id)
    employee = Employee.query.filter_by(user_id=user.id).first()
    user_pharmacies = UserPharmacy.query.filter_by(user_id=user.id).all()
    
    return render_template('users/view.html', user=user, employee=employee, user_pharmacies=user_pharmacies)

@users_bp.route('/toggle-status/<int:id>', methods=['GET', 'POST'])
@require_permission('manage_users')
def toggle_status(id):
    user = User.query.get_or_404(id)
    user.is_active = not user.is_active
    
    audit = Audit(
        user_id=current_user.id,
        action='toggle_user_status',
        entity_type='user',
        entity_id=user.id,
        details=f'Statut utilisateur changé: {user.username} -> {"Actif" if user.is_active else "Inactif"}',
        ip_address=request.remote_addr
    )
    db.session.add(audit)
    
    db.session.commit()
    
    flash(f'Utilisateur {"activé" if user.is_active else "désactivé"} avec succès!', 'success')
    return redirect(url_for('users.index'))

@users_bp.route('/login-history/<int:id>')
@require_permission('manage_users')
def login_history(id):
    """View user login history"""
    user = User.query.get_or_404(id)
    # Implementation would go here - depends on your login tracking system
    return render_template('users/login_history.html', user=user)

@users_bp.route('/activity-log/<int:id>')
@require_permission('manage_users')
def activity_log(id):
    """View user activity log"""
    user = User.query.get_or_404(id)
    audits = Audit.query.filter_by(user_id=user.id).order_by(Audit.created_at.desc()).limit(50).all()
    return render_template('users/activity_log.html', user=user, audits=audits)

@users_bp.route('/reset-password/<int:id>', methods=['GET', 'POST'])
@require_permission('manage_users')
def reset_password(id):
    """Reset user password"""
    user = User.query.get_or_404(id)
    
    if request.method == 'POST':
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if password != confirm_password:
            flash('Les mots de passe ne correspondent pas!', 'danger')
            return render_template('users/reset_password.html', user=user)
        
        user.set_password(password)
        
        audit = Audit(
            user_id=current_user.id,
            action='reset_password',
            entity_type='user',
            entity_id=user.id,
            details=f'Mot de passe réinitialisé pour: {user.username}',
            ip_address=request.remote_addr
        )
        db.session.add(audit)
        db.session.commit()
        
        flash('Mot de passe réinitialisé avec succès!', 'success')
        return redirect(url_for('users.index'))
    
    return render_template('users/reset_password.html', user=user)

@users_bp.route('/manage-permissions/<int:id>', methods=['GET', 'POST'])
@require_permission('manage_users')
def manage_permissions(id):
    """Manage user permissions"""
    user = User.query.get_or_404(id)
    
    if request.method == 'POST':
        perms = {}
        for perm, _ in PERMISSIONS:
            perms[perm] = request.form.get(f'perm_{perm}') == 'on'
        # Ne pas écraser par {} si rien n'est coché
        if any(perms.values()) or any(k.startswith('perm_') for k in request.form.keys()):
            user.set_permissions(perms)
        
        audit = Audit(
            user_id=current_user.id,
            action='update_permissions',
            entity_type='user',
            entity_id=user.id,
            details=f'Permissions modifiées pour: {user.username}',
            ip_address=request.remote_addr
        )
        db.session.add(audit)
        db.session.commit()
        
        flash('Permissions modifiées avec succès!', 'success')
        return redirect(url_for('users.index'))
    
    return render_template('users/manage_permissions.html', user=user, permissions=PERMISSIONS, permissions_by_module=PERMISSIONS_BY_MODULE)

@users_bp.route('/assign-pharmacies/<int:id>', methods=['GET', 'POST'])
@require_permission('manage_users')
def assign_pharmacies(id):
    """Assign pharmacies to user"""
    user = User.query.get_or_404(id)
    all_pharmacies = Pharmacy.query.all()
    user_pharmacies = UserPharmacy.query.filter_by(user_id=user.id).all()
    assigned_pharmacy_ids = [up.pharmacy_id for up in user_pharmacies]
    
    if request.method == 'POST':
        # Remove all existing assignments
        UserPharmacy.query.filter_by(user_id=user.id).delete()
        
        # Add new assignments
        pharmacy_ids = request.form.getlist('pharmacy_ids')
        is_primary = request.form.get('primary_pharmacy')
        
        for pharmacy_id in pharmacy_ids:
            user_pharmacy = UserPharmacy(
                user_id=user.id,
                pharmacy_id=int(pharmacy_id),
                is_primary=(str(pharmacy_id) == is_primary)
            )
            db.session.add(user_pharmacy)
        
        audit = Audit(
            user_id=current_user.id,
            action='assign_pharmacies',
            entity_type='user',
            entity_id=user.id,
            details=f'Pharmacies assignées pour: {user.username}',
            ip_address=request.remote_addr
        )
        db.session.add(audit)
        db.session.commit()
        
        flash('Pharmacies assignées avec succès!', 'success')
        return redirect(url_for('users.index'))
    
    return render_template('users/assign_pharmacies.html', user=user, all_pharmacies=all_pharmacies, assigned_pharmacy_ids=assigned_pharmacy_ids)

@users_bp.route('/change-role/<int:id>', methods=['GET', 'POST'])
@require_permission('manage_users')
def change_role(id):
    """Change user role"""
    user = User.query.get_or_404(id)
    
    if request.method == 'POST':
        new_role = request.form.get('role')
        user.role = new_role
        
        # Update employee position if exists
        employee = Employee.query.filter_by(user_id=user.id).first()
        if employee:
            employee.position = new_role.capitalize()
        
        audit = Audit(
            user_id=current_user.id,
            action='change_role',
            entity_type='user',
            entity_id=user.id,
            details=f'Rôle changé pour: {user.username} -> {new_role}',
            ip_address=request.remote_addr
        )
        db.session.add(audit)
        db.session.commit()
        
        flash('Rôle changé avec succès!', 'success')
        return redirect(url_for('users.index'))
    
    return render_template('users/change_role.html', user=user, roles=ROLES)

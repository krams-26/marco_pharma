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
            
            perms = {}
            for perm, _ in PERMISSIONS:
                perms[perm] = request.form.get(f'perm_{perm}') == 'on'
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
    return render_template('users/edit.html', user=user, permissions=PERMISSIONS, permissions_by_module=PERMISSIONS_BY_MODULE, roles=ROLES, pharmacies=pharmacies)

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

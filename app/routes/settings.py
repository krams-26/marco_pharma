from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from flask_login import login_required, current_user
from app.models import (
    db, Setting, ExchangeRate, Audit, SystemConfig, User, Product, ProductBatch,
    BatchMovement, Customer, Sale, SaleItem, Payment, SalePayment, StockMovement,
    Employee, Absence, SalaryPayment, LeaveRequest, CreditRequest, CashTransaction,
    Expense, Proforma, ProformaItem, Pharmacy, UserPharmacy, Notification,
    ValidationCode, EmployeeEvaluation, EvaluationCriteria, Task, Approval,
    Supplier, SaleCredit, CreditPayment, CreditTerms, TempSale
)
from app.decorators import require_permission

settings_bp = Blueprint('settings', __name__, url_prefix='/settings')

@settings_bp.route('/')
@require_permission('manage_settings')
def index():
    settings = Setting.query.all()
    settings_dict = {}
    for s in settings:
        # Convertir les valeurs booléennes string en booléens Python
        if s.value == 'true':
            settings_dict[s.key] = True
        elif s.value == 'false':
            settings_dict[s.key] = False
        else:
            settings_dict[s.key] = s.value
    
    # Récupérer le taux de change actuel
    current_rate = ExchangeRate.query.filter_by(is_active=True).first()
    
    # Récupérer tous les taux de change pour l'historique
    exchange_rates = ExchangeRate.query.order_by(ExchangeRate.created_at.desc()).all()
    
    # Récupérer le paramètre tab pour activer l'onglet approprié
    default_tab = request.args.get('tab', 'general')
    
    return render_template('settings/index.html', 
                         settings=settings_dict,
                         current_rate=current_rate,
                         exchange_rates=exchange_rates,
                         default_tab=default_tab)

@settings_bp.route('/update', methods=['POST'])
@require_permission('manage_settings')
def update():
    try:
        for key in ['company_name', 'company_address', 'company_phone', 'company_email', 
                   'currency_symbol', 'currency_code', 'tax_rate']:
            value = request.form.get(key, '')
            setting = Setting.query.filter_by(key=key).first()
            if setting:
                setting.value = value
            else:
                setting = Setting(key=key, value=value)
                db.session.add(setting)
        
        audit = Audit(
            user_id=current_user.id,
            action='update_settings',
            entity_type='settings',
            details='Paramètres mis à jour',
            ip_address=request.remote_addr
        )
        db.session.add(audit)
        
        db.session.commit()
        flash('Paramètres mis à jour avec succès!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erreur: {str(e)}', 'danger')
    
    return redirect(url_for('settings.index'))

@settings_bp.route('/save', methods=['POST'])
@require_permission('manage_settings')
def save():
    """Sauvegarder les paramètres via API JSON"""
    try:
        data = request.get_json()
        
        # Sauvegarder les paramètres généraux
        if 'general' in data:
            for key, value in data['general'].items():
                setting = Setting.query.filter_by(key=key).first()
                if setting:
                    setting.value = str(value)
                else:
                    setting = Setting(key=key, value=str(value))
                    db.session.add(setting)
        
        # Sauvegarder les paramètres de stock
        if 'stock' in data:
            for key, value in data['stock'].items():
                # Convertir les booléens en string pour le stockage
                if isinstance(value, bool):
                    value = 'true' if value else 'false'
                setting = Setting.query.filter_by(key=key).first()
                if setting:
                    setting.value = str(value)
                else:
                    setting = Setting(key=key, value=str(value))
                    db.session.add(setting)
        
        # Sauvegarder les paramètres de profil
        if 'profile' in data:
            profile_data = data['profile']
            
            # Mettre à jour les informations de l'utilisateur directement dans la table User
            if 'user_fullname' in profile_data:
                # Séparer le nom complet en prénom et nom
                fullname = profile_data['user_fullname'].strip()
                if fullname:
                    parts = fullname.split(' ', 1)
                    current_user.first_name = parts[0]
                    current_user.last_name = parts[1] if len(parts) > 1 else ''
            
            if 'user_email' in profile_data:
                # Vérifier que l'email n'est pas déjà utilisé par un autre utilisateur
                email = profile_data['user_email'].strip()
                if email:
                    # Valider le format de l'email
                    import re
                    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
                    if not re.match(email_pattern, email):
                        return jsonify({'success': False, 'message': 'Format d\'email invalide'}), 400
                    
                    # Vérifier l'unicité
                    existing_user = User.query.filter_by(email=email).first()
                    if existing_user and existing_user.id != current_user.id:
                        return jsonify({'success': False, 'message': 'Cet email est déjà utilisé par un autre utilisateur'}), 400
                    current_user.email = email
            
            if 'user_phone' in profile_data:
                # Le téléphone peut être stocké dans la table User ou Setting
                current_user.phone = profile_data['user_phone'].strip() if profile_data['user_phone'] else None
            
            # Sauvegarder les autres paramètres de profil dans Setting
            for key, value in profile_data.items():
                if key not in ['user_fullname', 'user_email', 'user_phone']:
                    setting = Setting.query.filter_by(key=key).first()
                    if setting:
                        setting.value = str(value)
                    else:
                        setting = Setting(key=key, value=str(value))
                        db.session.add(setting)
        
        # Sauvegarder les paramètres de sécurité
        if 'security' in data:
            for key, value in data['security'].items():
                # Convertir les booléens en string pour le stockage
                if isinstance(value, bool):
                    value = 'true' if value else 'false'
                setting = Setting.query.filter_by(key=key).first()
                if setting:
                    setting.value = str(value)
                else:
                    setting = Setting(key=key, value=str(value))
                    db.session.add(setting)
        
        # Sauvegarder les paramètres de notifications
        if 'notifications' in data:
            for key, value in data['notifications'].items():
                # Convertir les booléens en string pour le stockage
                if isinstance(value, bool):
                    value = 'true' if value else 'false'
                setting = Setting.query.filter_by(key=key).first()
                if setting:
                    setting.value = str(value)
                else:
                    setting = Setting(key=key, value=str(value))
                    db.session.add(setting)
        
        # Audit
        audit = Audit(
            user_id=current_user.id,
            action='update_settings_api',
            entity_type='settings',
            details='Paramètres mis à jour via API',
            ip_address=request.remote_addr
        )
        db.session.add(audit)
        
        db.session.commit()
        return jsonify({'success': True, 'message': 'Paramètres sauvegardés avec succès!'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Erreur: {str(e)}'}), 500

@settings_bp.route('/update-exchange-rate', methods=['POST'])
@require_permission('manage_settings')
def update_exchange_rate():
    """Mettre à jour le taux de change via API"""
    try:
        data = request.get_json()
        new_rate = data.get('rate')
        
        if not new_rate or new_rate <= 0:
            return jsonify({'success': False, 'message': 'Taux invalide'}), 400
        
        # Désactiver tous les taux existants
        ExchangeRate.query.update({'is_active': False})
        
        # Créer un nouveau taux actif
        exchange_rate = ExchangeRate(
            from_currency='USD',
            to_currency='CDF',
            rate=new_rate,
            is_active=True
        )
        db.session.add(exchange_rate)
        
        # Audit
        audit = Audit(
            user_id=current_user.id,
            action='update_exchange_rate',
            entity_type='exchange_rate',
            details=f'Taux de change mis à jour: {new_rate} CDF pour 1 USD',
            ip_address=request.remote_addr
        )
        db.session.add(audit)
        
        db.session.commit()
        return jsonify({'success': True, 'message': 'Taux de change mis à jour avec succès!'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Erreur: {str(e)}'}), 500

@settings_bp.route('/get-logo', methods=['GET'])
@require_permission('manage_settings')
def get_logo():
    """Récupérer le logo de l'entreprise"""
    try:
        logo_setting = Setting.query.filter_by(key='company_logo').first()
        if logo_setting and logo_setting.value:
            return jsonify({'success': True, 'logo': logo_setting.value})
        else:
            return jsonify({'success': False, 'logo': None})
    except Exception as e:
        return jsonify({'success': False, 'message': f'Erreur: {str(e)}'}), 500

@settings_bp.route('/activate-rate/<int:rate_id>', methods=['POST'])
@require_permission('manage_settings')
def activate_rate(rate_id):
    """Activer un taux de change"""
    try:
        rate = ExchangeRate.query.get_or_404(rate_id)
        
        # Désactiver tous les autres taux
        ExchangeRate.query.update({'is_active': False})
        
        # Activer le taux sélectionné
        rate.is_active = True
        rate.updated_at = db.func.now()
        
        # Audit
        audit = Audit(
            user_id=current_user.id,
            action='activate_exchange_rate',
            entity_type='exchange_rate',
            details=f'Taux de change activé: {rate.rate} CDF pour 1 USD',
            ip_address=request.remote_addr
        )
        db.session.add(audit)
        
        db.session.commit()
        return jsonify({'success': True, 'message': 'Taux activé avec succès!'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Erreur: {str(e)}'}), 500

@settings_bp.route('/delete-rate/<int:rate_id>', methods=['POST'])
@require_permission('manage_settings')
def delete_rate(rate_id):
    """Supprimer un taux de change"""
    try:
        rate = ExchangeRate.query.get_or_404(rate_id)
        
        # Ne pas permettre la suppression du taux actif
        if rate.is_active:
            return jsonify({'success': False, 'message': 'Impossible de supprimer le taux actif'}), 400
        
        # Audit
        audit = Audit(
            user_id=current_user.id,
            action='delete_exchange_rate',
            entity_type='exchange_rate',
            details=f'Taux de change supprimé: {rate.rate} CDF',
            ip_address=request.remote_addr
        )
        db.session.add(audit)
        
        db.session.delete(rate)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Taux supprimé avec succès!'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Erreur: {str(e)}'}), 500

@settings_bp.route('/exchange-rates', methods=['GET', 'POST'])
@require_permission('manage_settings')
def exchange_rates():
    if request.method == 'POST':
        try:
            from_currency = request.form.get('from_currency')
            to_currency = request.form.get('to_currency')
            rate = float(request.form.get('rate'))
            
            # Désactiver tous les autres taux USD→CDF
            if from_currency == 'USD' and to_currency == 'CDF':
                ExchangeRate.query.filter_by(
                    from_currency='USD',
                    to_currency='CDF'
                ).update({'is_active': False})
            
            exchange_rate = ExchangeRate.query.filter_by(
                from_currency=from_currency,
                to_currency=to_currency
            ).first()
            
            if exchange_rate:
                exchange_rate.rate = rate
                exchange_rate.is_active = True  # Activer automatiquement
            else:
                exchange_rate = ExchangeRate(
                    from_currency=from_currency,
                    to_currency=to_currency,
                    rate=rate,
                    is_active=True  # Activer par défaut
                )
                db.session.add(exchange_rate)
            
            # Audit
            audit = Audit(
                user_id=current_user.id,
                action='update_exchange_rate',
                entity_type='exchange_rate',
                entity_id=exchange_rate.id,
                details=f'Taux {from_currency}→{to_currency} mis à jour: {rate}',
                ip_address=request.remote_addr
            )
            db.session.add(audit)
            
            db.session.commit()
            flash(f'Taux de change mis à jour et activé: 1 {from_currency} = {rate} {to_currency}', 'success')
            # Pattern PRG: éviter re-soumission et garantir l'état mis à jour
            return redirect(url_for('settings.exchange_rates'))
        except Exception as e:
            db.session.rollback()
            flash(f'Erreur: {str(e)}', 'danger')
            return redirect(url_for('settings.exchange_rates'))
    
    rates = ExchangeRate.query.order_by(ExchangeRate.created_at.desc()).all()
    current_rate = ExchangeRate.query.filter_by(from_currency='USD', to_currency='CDF', is_active=True).first()
    active_rate_id = current_rate.id if current_rate else (rates[0].id if len(rates) > 0 else None)
    return render_template('settings/exchange_rates.html', rates=rates, current_rate=current_rate, active_rate_id=active_rate_id)

@settings_bp.route('/system-config')
@require_permission('manage_settings')
def system_config():
    """Gérer les configurations système"""
    configs = SystemConfig.query.order_by(SystemConfig.category, SystemConfig.key).all()
    
    # Grouper par catégorie
    by_category = {}
    for config in configs:
        if config.category not in by_category:
            by_category[config.category] = []
        by_category[config.category].append(config)
    
    return render_template('settings/system_config.html', configs_by_category=by_category)

@settings_bp.route('/system-config/update', methods=['POST'])
@require_permission('manage_settings')
def update_system_config():
    """Mettre à jour les configurations système"""
    try:
        data = request.get_json()
        
        for key, value in data.items():
            SystemConfig.set(key, value)
        
        # Audit
        audit = Audit(
            user_id=current_user.id,
            action='update_system_config',
            entity_type='system_config',
            details=f'Configurations système mises à jour',
            ip_address=request.remote_addr
        )
        db.session.add(audit)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Configurations mises à jour avec succès!'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Erreur: {str(e)}'}), 500

@settings_bp.route('/reset-database', methods=['POST'])
@require_permission('manage_settings')
def reset_database():
    """Réinitialiser toutes les données de la base de données sauf le compte admin"""
    try:
        # Vérifier que l'utilisateur est bien admin
        if current_user.role != 'admin':
            return jsonify({'success': False, 'message': 'Seul un administrateur peut réinitialiser la base de données'}), 403
        
        # Récupérer l'ID de l'admin actuel
        admin_user = current_user
        
        # Enregistrer d'abord l'audit de réinitialisation (avant de supprimer les autres audits)
        reset_audit = Audit(
            user_id=admin_user.id,
            action='reset_database',
            module='settings',
            action_type='delete',
            entity_type='database',
            details=f'Réinitialisation complète de la base de données par {admin_user.username}',
            result='success',
            ip_address=request.remote_addr
        )
        db.session.add(reset_audit)
        db.session.flush()  # Enregistrer l'audit avant de continuer
        
        # Supprimer toutes les données dans l'ordre correct (en respectant les foreign keys)
        # Supprimer tous les audits sauf celui que nous venons de créer
        Audit.query.filter(Audit.id != reset_audit.id).delete()
        
        # Supprimer les notifications
        Notification.query.delete()
        
        # Supprimer les ventes et leurs éléments
        SaleItem.query.delete()
        SalePayment.query.delete()
        Payment.query.delete()
        Sale.query.delete()
        
        # Supprimer les proformas
        ProformaItem.query.delete()
        Proforma.query.delete()
        
        # Supprimer les ventes à crédit
        CreditPayment.query.delete()
        SaleCredit.query.delete()
        
        # Supprimer les paiements partiels
        SalePayment.query.delete()
        
        # Supprimer les mouvements de stock
        BatchMovement.query.delete()
        StockMovement.query.delete()
        
        # Supprimer les lots
        ProductBatch.query.delete()
        
        # Supprimer les produits
        Product.query.delete()
        
        # Supprimer les clients
        Customer.query.delete()
        
        # Supprimer les fournisseurs
        Supplier.query.delete()
        
        # Supprimer les transactions de caisse
        CashTransaction.query.delete()
        
        # Supprimer les dépenses
        Expense.query.delete()
        
        # Supprimer les données RH
        CreditRequest.query.delete()
        LeaveRequest.query.delete()
        SalaryPayment.query.delete()
        Absence.query.delete()
        EmployeeEvaluation.query.delete()
        Employee.query.delete()
        
        # Supprimer les tâches
        Task.query.delete()
        
        # Supprimer les approbations
        Approval.query.delete()
        
        # Supprimer les codes de validation
        ValidationCode.query.delete()
        
        # Supprimer les ventes temporaires
        TempSale.query.delete()
        
        # Supprimer les critères d'évaluation
        EvaluationCriteria.query.delete()
        
        # Supprimer les termes de crédit
        CreditTerms.query.delete()
        
        # Supprimer les assignations de pharmacies (sauf pour l'admin)
        UserPharmacy.query.filter(UserPharmacy.user_id != admin_user.id).delete()
        
        # Supprimer les pharmacies (optionnel - vous pouvez les garder si nécessaire)
        # Pharmacy.query.delete()
        
        # Supprimer tous les utilisateurs sauf l'admin
        User.query.filter(User.id != admin_user.id).delete()
        
        # Garder les paramètres système (Settings, SystemConfig, ExchangeRate peuvent être conservés ou réinitialisés)
        # Pour une réinitialisation complète, on peut aussi les supprimer
        
        # Optionnel: Réinitialiser les taux de change (garder le dernier actif ou supprimer)
        # ExchangeRate.query.delete()
        
        # Le commit final (l'audit est déjà ajouté et flushé)
        db.session.commit()
        
        return jsonify({
            'success': True, 
            'message': 'Base de données réinitialisée avec succès! Seul le compte administrateur a été conservé.'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Erreur lors de la réinitialisation: {str(e)}'}), 500


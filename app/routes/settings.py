from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from app.models import db, Setting, ExchangeRate, Audit
from app.decorators import require_permission

settings_bp = Blueprint('settings', __name__, url_prefix='/settings')

@settings_bp.route('/')
@require_permission('manage_settings')
def index():
    settings = Setting.query.all()
    settings_dict = {s.key: s.value for s in settings}
    
    exchange_rates = ExchangeRate.query.all()
    
    return render_template('settings/index.html', 
                         settings=settings_dict,
                         exchange_rates=exchange_rates)

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

@settings_bp.route('/activate-rate/<int:id>', methods=['POST'])
@require_permission('manage_settings')
def activate_rate(id):
    """Activer un taux de change"""
    try:
        rate = ExchangeRate.query.get_or_404(id)
        
        # Désactiver tous les autres taux de la même paire
        ExchangeRate.query.filter_by(
            from_currency=rate.from_currency,
            to_currency=rate.to_currency
        ).update({'is_active': False})
        
        # Activer ce taux
        rate.is_active = True
        
        # Audit
        audit = Audit(
            user_id=current_user.id,
            action='activate_exchange_rate',
            entity_type='exchange_rate',
            entity_id=rate.id,
            details=f'Taux activé: {rate.from_currency}→{rate.to_currency} = {rate.rate}',
            ip_address=request.remote_addr
        )
        db.session.add(audit)
        
        db.session.commit()
        flash(f'Taux activé: 1 {rate.from_currency} = {rate.rate} {rate.to_currency}', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erreur: {str(e)}', 'danger')
    
    return redirect(url_for('settings.exchange_rates'))

@settings_bp.route('/delete-rate/<int:id>', methods=['POST'])
@require_permission('manage_settings')
def delete_rate(id):
    rate = ExchangeRate.query.get_or_404(id)
    
    if rate.is_active:
        flash('Impossible de supprimer un taux actif!', 'danger')
        return redirect(url_for('settings.exchange_rates'))
    
    db.session.delete(rate)
    db.session.commit()
    flash('Taux de change supprimé!', 'success')
    return redirect(url_for('settings.exchange_rates'))

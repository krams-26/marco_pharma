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
            
            exchange_rate = ExchangeRate.query.filter_by(
                from_currency=from_currency,
                to_currency=to_currency
            ).first()
            
            if exchange_rate:
                exchange_rate.rate = rate
            else:
                exchange_rate = ExchangeRate(
                    from_currency=from_currency,
                    to_currency=to_currency,
                    rate=rate
                )
                db.session.add(exchange_rate)
            
            db.session.commit()
            flash('Taux de change mis à jour!', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Erreur: {str(e)}', 'danger')
    
    rates = ExchangeRate.query.all()
    return render_template('settings/exchange_rates.html', rates=rates)

@settings_bp.route('/delete-rate/<int:id>', methods=['POST'])
@require_permission('manage_settings')
def delete_rate(id):
    rate = ExchangeRate.query.get_or_404(id)
    db.session.delete(rate)
    db.session.commit()
    flash('Taux de change supprimé!', 'success')
    return redirect(url_for('settings.exchange_rates'))

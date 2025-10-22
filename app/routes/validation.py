from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from app.models import db, ValidationCode, User, Notification, Audit
from app.validation_helper import generate_validation_code, validate_code, clean_expired_codes
from app.decorators import require_permission
from datetime import datetime

validation_bp = Blueprint('validation', __name__, url_prefix='/validation')

@validation_bp.route('/request', methods=['POST'])
@login_required
def request_code():
    """Demander un code de validation"""
    try:
        data = request.get_json() if request.is_json else request.form
        
        admin = User.query.filter_by(role='admin', is_active=True).first()
        if not admin:
            return jsonify({'success': False, 'message': 'Aucun administrateur disponible'}), 404
        
        code = generate_validation_code(
            generated_by=current_user.id,
            generated_for=admin.id,
            reference_type=data.get('reference_type', 'sale'),
            reference_id=data.get('reference_id'),
            code_type=data.get('type', 'status_change'),
            expiry_minutes=int(data.get('expiry_minutes', 30))
        )
        
        if not code:
            return jsonify({'success': False, 'message': 'Erreur génération code'}), 500
        
        return jsonify({
            'success': True,
            'message': f'Code demandé. Contactez l\'administrateur.',
            'code_id': code.id,
            'expires_at': code.expires_at.strftime('%d/%m/%Y %H:%M')
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@validation_bp.route('/validate', methods=['POST'])
@login_required
def validate():
    """Valider un code"""
    try:
        data = request.get_json() if request.is_json else request.form
        
        code = data.get('code', '').upper()
        reference_type = data.get('reference_type')
        reference_id = data.get('reference_id')
        
        is_valid = validate_code(code, reference_type, reference_id, current_user.id)
        
        if is_valid:
            return jsonify({'success': True, 'message': 'Code validé avec succès'})
        else:
            return jsonify({'success': False, 'message': 'Code invalide ou expiré'}), 400
            
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@validation_bp.route('/my-codes')
@login_required
def my_codes():
    """Codes générés pour l'utilisateur connecté"""
    codes = ValidationCode.query.filter_by(generated_for=current_user.id).order_by(ValidationCode.created_at.desc()).limit(20).all()
    
    return render_template('validation/my_codes.html', codes=codes)

@validation_bp.route('/admin-codes')
@require_permission('manage_settings')
def admin_codes():
    """Tous les codes (admin seulement)"""
    from app.decorators import require_permission
    
    page = request.args.get('page', 1, type=int)
    filter_status = request.args.get('status', '')
    
    query = ValidationCode.query
    
    if filter_status:
        query = query.filter_by(status=filter_status)
    
    codes = query.order_by(ValidationCode.created_at.desc()).paginate(
        page=page, per_page=6, error_out=False
    )
    
    stats = {
        'active': ValidationCode.query.filter_by(status='active').count(),
        'used': ValidationCode.query.filter_by(status='used').count(),
        'expired': ValidationCode.query.filter_by(status='expired').count()
    }
    
    return render_template('validation/admin_codes.html', codes=codes, stats=stats, filter_status=filter_status)

@validation_bp.route('/cleanup', methods=['POST'])
@require_permission('manage_settings')
def cleanup():
    """Nettoyer les codes expirés"""
    from app.decorators import require_permission
    
    try:
        clean_expired_codes()
        flash('Codes expirés nettoyés avec succès!', 'success')
    except Exception as e:
        flash(f'Erreur: {str(e)}', 'danger')
    
    return redirect(url_for('validation.admin_codes'))


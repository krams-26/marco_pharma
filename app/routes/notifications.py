from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from app.models import db, Notification, User, Audit
from app.decorators import require_permission
from datetime import datetime
from app.pharmacy_utils import filter_by_pharmacy, get_accessible_pharmacies, is_admin
from app.export_utils import export_to_csv, export_to_excel

notifications_bp = Blueprint('notifications', __name__, url_prefix='/notifications')

@notifications_bp.route('/')
@login_required
def index():
    page = request.args.get('page', 1, type=int)
    filter_status = request.args.get('status', '')
    filter_type = request.args.get('type', '')
    
    query = Notification.query.filter(
        db.or_(
            Notification.target_admin_id == current_user.id,
            Notification.target_admin_id == None
        )
    )
    
    if filter_status:
        query = query.filter_by(status=filter_status)
    
    if filter_type:
        query = query.filter_by(type=filter_type)
    
    notifications = query.order_by(Notification.created_at.desc()).paginate(
        page=page, per_page=6, error_out=False
    )
    
    stats = {
        'total': Notification.query.filter(
            db.or_(
                Notification.target_admin_id == current_user.id,
                Notification.target_admin_id == None
            )
        ).count(),
        'unread': Notification.query.filter(
            db.or_(
                Notification.target_admin_id == current_user.id,
                Notification.target_admin_id == None
            ),
            Notification.read_at == None
        ).count(),
        'urgent': Notification.query.filter(
            db.or_(
                Notification.target_admin_id == current_user.id,
                Notification.target_admin_id == None
            ),
            Notification.priority == 'urgent',
            Notification.status == 'pending'
        ).count()
    }
    
    return render_template('notifications/index.html', 
                         notifications=notifications, 
                         stats=stats,
                         filter_status=filter_status,
                         filter_type=filter_type)

@notifications_bp.route('/unread-count')
@login_required
def unread_count():
    count = Notification.query.filter(
        db.or_(
            Notification.target_admin_id == current_user.id,
            Notification.target_admin_id == None
        ),
        Notification.read_at == None,
        Notification.status == 'pending'
    ).count()
    
    return jsonify({'count': count})

@notifications_bp.route('/recent')
@login_required
def recent():
    notifications = Notification.query.filter(
        db.or_(
            Notification.target_admin_id == current_user.id,
            Notification.target_admin_id == None
        )
    ).order_by(Notification.created_at.desc()).limit(5).all()
    
    return jsonify([{
        'id': n.id,
        'title': n.title,
        'message': n.message,
        'type': n.type,
        'priority': n.priority,
        'read': n.read_at is not None,
        'created_at': n.created_at.strftime('%d/%m/%Y %H:%M')
    } for n in notifications])

@notifications_bp.route('/mark-read/<int:id>', methods=['POST'])
@login_required
def mark_read(id):
    notification = Notification.query.get_or_404(id)
    
    if notification.target_admin_id and notification.target_admin_id != current_user.id:
        return jsonify({'success': False, 'message': 'Non autorisé'}), 403
    
    try:
        notification.read_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@notifications_bp.route('/mark-all-read', methods=['POST'])
@login_required
def mark_all_read():
    try:
        Notification.query.filter(
            db.or_(
                Notification.target_admin_id == current_user.id,
                Notification.target_admin_id == None
            ),
            Notification.read_at == None
        ).update({'read_at': datetime.utcnow()})
        
        db.session.commit()
        
        flash('Toutes les notifications marquées comme lues!', 'success')
        return redirect(url_for('notifications.index'))
    except Exception as e:
        db.session.rollback()
        flash(f'Erreur: {str(e)}', 'danger')
        return redirect(url_for('notifications.index'))

@notifications_bp.route('/create', methods=['POST'])
@login_required
def create():
    try:
        data = request.get_json() if request.is_json else request.form
        
        notification = Notification(
            type=data.get('type', 'system_alert'),
            title=data.get('title'),
            message=data.get('message'),
            requester_id=current_user.id,
            target_admin_id=data.get('target_admin_id'),
            priority=data.get('priority', 'medium'),
            action_required=data.get('action_required'),
            reference_type=data.get('reference_type'),
            reference_id=data.get('reference_id'),
            status='pending'
        )
        
        db.session.add(notification)
        db.session.commit()
        
        if request.is_json:
            return jsonify({'success': True, 'notification_id': notification.id})
        else:
            flash('Notification créée!', 'success')
            return redirect(url_for('notifications.index'))
            
    except Exception as e:
        db.session.rollback()
        if request.is_json:
            return jsonify({'success': False, 'message': str(e)}), 500
        else:
            flash(f'Erreur: {str(e)}', 'danger')
            return redirect(url_for('notifications.index'))


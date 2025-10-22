from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from app.models import Audit, User, db
from app.decorators import require_permission
from datetime import datetime, timedelta
from app.pharmacy_utils import filter_by_pharmacy, get_accessible_pharmacies, is_admin
from app.export_utils import export_to_csv, export_to_excel
from sqlalchemy import func, and_

audits_bp = Blueprint('audits', __name__, url_prefix='/audits')


@audits_bp.route('/')
@require_permission('view_audits')
def index():
    """Liste des audits avec filtres avancés"""
    page = request.args.get('page', 1, type=int)
    user_id = request.args.get('user_id')
    action = request.args.get('action')
    module = request.args.get('module')
    action_type = request.args.get('action_type')
    result = request.args.get('result')
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    search = request.args.get('search', '')
    
    query = Audit.query
    
    # Filtres
    if user_id:
        query = query.filter_by(user_id=user_id)
    if action:
        query = query.filter(Audit.action.ilike(f'%{action}%'))
    if module and module != 'all':
        query = query.filter_by(module=module)
    if action_type and action_type != 'all':
        query = query.filter_by(action_type=action_type)
    if result and result != 'all':
        query = query.filter_by(result=result)
    if date_from:
        query = query.filter(Audit.created_at >= datetime.strptime(date_from, '%Y-%m-%d'))
    if date_to:
        query = query.filter(Audit.created_at <= datetime.strptime(date_to + ' 23:59:59', '%Y-%m-%d %H:%M:%S'))
    if search:
        query = query.filter(
            db.or_(
                Audit.action.ilike(f'%{search}%'),
                Audit.details.ilike(f'%{search}%')
            )
        )
    
    audits = query.order_by(Audit.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    
    # Récupérer les utilisateurs pour le filtre
    users = User.query.all()
    
    # Récupérer les modules et types uniques
    modules = db.session.query(Audit.module).distinct().filter(Audit.module.isnot(None)).all()
    modules = [m[0] for m in modules]
    
    action_types = db.session.query(Audit.action_type).distinct().filter(Audit.action_type.isnot(None)).all()
    action_types = [a[0] for a in action_types]
    
    return render_template('audits/index.html', 
                         audits=audits, 
                         users=users,
                         modules=modules,
                         action_types=action_types,
                         filters={
                             'user_id': user_id,
                             'action': action,
                             'module': module,
                             'action_type': action_type,
                             'result': result,
                             'date_from': date_from,
                             'date_to': date_to,
                             'search': search
                         })


@audits_bp.route('/dashboard')
@require_permission('view_audits')
def dashboard():
    """Dashboard avec statistiques et graphiques"""
    # Période par défaut: 30 derniers jours
    days = request.args.get('days', 30, type=int)
    date_from = datetime.now() - timedelta(days=days)
    
    # Statistiques générales
    total_audits = Audit.query.filter(Audit.created_at >= date_from).count()
    
    # Par type d'action
    by_action_type = db.session.query(
        Audit.action_type,
        func.count(Audit.id).label('count')
    ).filter(
        Audit.created_at >= date_from,
        Audit.action_type.isnot(None)
    ).group_by(Audit.action_type).all()
    
    # Par module
    by_module = db.session.query(
        Audit.module,
        func.count(Audit.id).label('count')
    ).filter(
        Audit.created_at >= date_from,
        Audit.module.isnot(None)
    ).group_by(Audit.module).order_by(func.count(Audit.id).desc()).limit(10).all()
    
    # Par résultat
    by_result = db.session.query(
        Audit.result,
        func.count(Audit.id).label('count')
    ).filter(
        Audit.created_at >= date_from
    ).group_by(Audit.result).all()
    
    # Utilisateurs les plus actifs
    top_users = db.session.query(
        User.username,
        func.count(Audit.id).label('count')
    ).join(User, Audit.user_id == User.id).filter(
        Audit.created_at >= date_from
    ).group_by(User.username).order_by(func.count(Audit.id).desc()).limit(10).all()
    
    # Activité par jour (derniers 30 jours)
    daily_activity = db.session.query(
        func.date(Audit.created_at).label('date'),
        func.count(Audit.id).label('count')
    ).filter(
        Audit.created_at >= date_from
    ).group_by(func.date(Audit.created_at)).order_by(func.date(Audit.created_at)).all()
    
    # Actions suspectes
    suspicious_count = Audit.query.filter(
        Audit.created_at >= date_from,
        db.or_(
            Audit.result == 'failed',
            Audit.result == 'denied'
        )
    ).count()
    
    # Dernières activités suspectes
    recent_suspicious = Audit.query.filter(
        Audit.created_at >= date_from,
        db.or_(
            Audit.result == 'failed',
            Audit.result == 'denied'
        )
    ).order_by(Audit.created_at.desc()).limit(10).all()
    
    return render_template('audits/dashboard.html',
                         total_audits=total_audits,
                         by_action_type=by_action_type,
                         by_module=by_module,
                         by_result=by_result,
                         top_users=top_users,
                         daily_activity=daily_activity,
                         suspicious_count=suspicious_count,
                         recent_suspicious=recent_suspicious,
                         days=days)


@audits_bp.route('/<int:id>')
@require_permission('view_audits')
def view(id):
    """Vue détaillée d'un audit avec comparaison avant/après"""
    audit = Audit.query.get_or_404(id)
    
    # Récupérer les changements si c'est une modification
    changes = None
    if audit.has_changes:
        changes = audit.get_changes()
    
    # Audits liés (même entité, même période ~1h)
    related_audits = None
    if audit.entity_id and audit.entity_type:
        time_range_start = audit.created_at - timedelta(hours=1)
        time_range_end = audit.created_at + timedelta(hours=1)
        
        related_audits = Audit.query.filter(
            and_(
                Audit.entity_type == audit.entity_type,
                Audit.entity_id == audit.entity_id,
                Audit.id != audit.id,
                Audit.created_at >= time_range_start,
                Audit.created_at <= time_range_end
            )
        ).order_by(Audit.created_at.desc()).limit(5).all()
    
    return render_template('audits/view.html', 
                         audit=audit, 
                         changes=changes,
                         related_audits=related_audits)


@audits_bp.route('/alerts')
@require_permission('view_audits')
def alerts():
    """Page des alertes d'activités suspectes"""
    page = request.args.get('page', 1, type=int)
    days = request.args.get('days', 7, type=int)
    
    date_from = datetime.now() - timedelta(days=days)
    
    # Récupérer les activités suspectes
    suspicious_query = Audit.query.filter(
        Audit.created_at >= date_from,
        db.or_(
            Audit.result == 'failed',
            Audit.result == 'denied'
        )
    )
    
    suspicious_audits = suspicious_query.order_by(Audit.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    
    # Statistiques
    stats = {
        'total': suspicious_query.count(),
        'failed': Audit.query.filter(
            Audit.created_at >= date_from,
            Audit.result == 'failed'
        ).count(),
        'denied': Audit.query.filter(
            Audit.created_at >= date_from,
            Audit.result == 'denied'
        ).count(),
        'login_failed': Audit.query.filter(
            Audit.created_at >= date_from,
            Audit.action_type == 'login',
            Audit.result == 'failed'
        ).count()
    }
    
    # Utilisateurs avec le plus d'échecs
    users_with_failures = db.session.query(
        User.username,
        func.count(Audit.id).label('count')
    ).join(User, Audit.user_id == User.id).filter(
        Audit.created_at >= date_from,
        Audit.result.in_(['failed', 'denied'])
    ).group_by(User.username).order_by(func.count(Audit.id).desc()).limit(5).all()
    
    return render_template('audits/alerts.html',
                         audits=suspicious_audits,
                         stats=stats,
                         users_with_failures=users_with_failures,
                         days=days)


@audits_bp.route('/export/<format>')
@require_permission('view_audits')
def export(format):
    """Exporter les audits"""
    # Récupérer les filtres
    user_id = request.args.get('user_id')
    module = request.args.get('module')
    action_type = request.args.get('action_type')
    result = request.args.get('result')
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    
    query = Audit.query
    
    if user_id:
        query = query.filter_by(user_id=user_id)
    if module and module != 'all':
        query = query.filter_by(module=module)
    if action_type and action_type != 'all':
        query = query.filter_by(action_type=action_type)
    if result and result != 'all':
        query = query.filter_by(result=result)
    if date_from:
        query = query.filter(Audit.created_at >= datetime.strptime(date_from, '%Y-%m-%d'))
    if date_to:
        query = query.filter(Audit.created_at <= datetime.strptime(date_to + ' 23:59:59', '%Y-%m-%d %H:%M:%S'))
    
    audits = query.order_by(Audit.created_at.desc()).all()
    
    headers = ['ID', 'Date/Heure', 'Utilisateur', 'Module', 'Action', 'Type', 'Entité', 'Détails', 'Résultat', 'IP']
    data = []
    
    for audit in audits:
        data.append({
            'ID': audit.id,
            'Date/Heure': audit.created_at.strftime('%d/%m/%Y %H:%M:%S'),
            'Utilisateur': audit.user.username if audit.user else 'Système',
            'Module': audit.module or '-',
            'Action': audit.action,
            'Type': audit.action_type or '-',
            'Entité': f"{audit.entity_type} #{audit.entity_id}" if audit.entity_id else '-',
            'Détails': audit.details or '-',
            'Résultat': audit.result,
            'IP': audit.ip_address or '-'
        })
    
    if format == 'csv':
        return export_to_csv(data, 'audits', headers)
    else:
        return export_to_excel(data, 'audits', headers, 'Audits')

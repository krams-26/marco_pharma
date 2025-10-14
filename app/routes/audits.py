from flask import Blueprint, render_template, request
from flask_login import login_required
from app.models import Audit
from app.decorators import require_permission
from datetime import datetime

audits_bp = Blueprint('audits', __name__, url_prefix='/audits')

@audits_bp.route('/')
@require_permission('view_audits')
def index():
    page = request.args.get('page', 1, type=int)
    user_id = request.args.get('user_id')
    action = request.args.get('action')
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    
    query = Audit.query
    
    if user_id:
        query = query.filter_by(user_id=user_id)
    if action:
        query = query.filter(Audit.action.ilike(f'%{action}%'))
    if date_from:
        query = query.filter(Audit.created_at >= datetime.strptime(date_from, '%Y-%m-%d'))
    if date_to:
        query = query.filter(Audit.created_at <= datetime.strptime(date_to, '%Y-%m-%d'))
    
    audits = query.order_by(Audit.created_at.desc()).paginate(
        page=page, per_page=50, error_out=False
    )
    
    return render_template('audits/index.html', audits=audits)

from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_required, current_user
from app import db
from app.models import Approval, User, Notification
from app.decorators import require_permission
from datetime import datetime
import json

approvals_bp = Blueprint('approvals', __name__, url_prefix='/approvals')

@approvals_bp.route('/')
@login_required
@require_permission('view_approvals')
def index():
    status_filter = request.args.get('status', 'all')
    type_filter = request.args.get('type', 'all')
    view_filter = request.args.get('view', 'all')
    
    query = Approval.query
    
    if view_filter == 'my_requests':
        query = query.filter_by(requested_by=current_user.id)
    elif view_filter == 'to_approve':
        query = query.filter_by(approver_id=current_user.id, status='pending')
    
    if status_filter != 'all':
        query = query.filter_by(status=status_filter)
    
    if type_filter != 'all':
        query = query.filter_by(request_type=type_filter)
    
    approvals = query.order_by(Approval.created_at.desc()).all()
    
    stats = {
        'total': Approval.query.count(),
        'pending': Approval.query.filter_by(status='pending').count(),
        'approved': Approval.query.filter_by(status='approved').count(),
        'rejected': Approval.query.filter_by(status='rejected').count(),
        'my_pending': Approval.query.filter_by(approver_id=current_user.id, status='pending').count()
    }
    
    return render_template('approvals/index.html', approvals=approvals, stats=stats)

@approvals_bp.route('/<int:id>')
@login_required
@require_permission('view_approvals')
def show(id):
    approval = Approval.query.get_or_404(id)
    
    try:
        if approval.request_data:
            approval.parsed_data = json.loads(approval.request_data)
        else:
            approval.parsed_data = {}
    except:
        approval.parsed_data = {}
    
    return render_template('approvals/show.html', approval=approval)

@approvals_bp.route('/create', methods=['POST'])
@login_required
def create():
    try:
        request_type = request.form.get('request_type')
        title = request.form.get('title')
        description = request.form.get('description')
        entity_type = request.form.get('entity_type')
        entity_id = request.form.get('entity_id')
        approver_id = request.form.get('approver_id')
        request_data = request.form.get('request_data', '{}')
        priority = request.form.get('priority', 'medium')
        
        if not all([request_type, title, approver_id]):
            return jsonify({'success': False, 'message': 'Données manquantes'}), 400
        
        primary_pharmacy = current_user.get_primary_pharmacy()
        
        approval = Approval(
            request_type=request_type,
            title=title,
            description=description,
            entity_type=entity_type,
            entity_id=int(entity_id) if entity_id else None,
            requested_by=current_user.id,
            approver_id=int(approver_id),
            pharmacy_id=primary_pharmacy.id if primary_pharmacy else None,
            request_data=request_data,
            priority=priority,
            status='pending'
        )
        
        db.session.add(approval)
        db.session.commit()
        
        notification = Notification(
            user_id=int(approver_id),
            type='approval_request',
            title='Nouvelle demande d\'approbation',
            message=f'{current_user.full_name} a créé une demande: {title}',
            related_entity='approval',
            related_id=approval.id
        )
        db.session.add(notification)
        db.session.commit()
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({
                'success': True,
                'message': 'Demande créée',
                'approval_id': approval.id
            })
        
        flash('Demande d\'approbation créée avec succès', 'success')
        return redirect(url_for('approvals.show', id=approval.id))
        
    except Exception as e:
        db.session.rollback()
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'message': str(e)}), 400
        flash(f'Erreur: {str(e)}', 'danger')
        return redirect(url_for('approvals.index'))

@approvals_bp.route('/<int:id>/approve', methods=['POST'])
@login_required
@require_permission('approve_requests')
def approve(id):
    approval = Approval.query.get_or_404(id)
    
    if approval.approver_id != current_user.id:
        flash('Vous n\'êtes pas autorisé à approuver cette demande', 'danger')
        return redirect(url_for('approvals.show', id=id))
    
    if approval.status != 'pending':
        flash('Cette demande a déjà été traitée', 'warning')
        return redirect(url_for('approvals.show', id=id))
    
    try:
        approval.status = 'approved'
        approval.approved_at = datetime.utcnow()
        
        notification = Notification(
            user_id=approval.requested_by,
            type='approval_status',
            title='Demande approuvée',
            message=f'Votre demande "{approval.title}" a été approuvée',
            related_entity='approval',
            related_id=approval.id
        )
        db.session.add(notification)
        db.session.commit()
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': True, 'message': 'Demande approuvée'})
        
        flash('Demande approuvée avec succès', 'success')
        return redirect(url_for('approvals.show', id=id))
        
    except Exception as e:
        db.session.rollback()
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'message': str(e)}), 400
        flash(f'Erreur: {str(e)}', 'danger')
        return redirect(url_for('approvals.show', id=id))

@approvals_bp.route('/<int:id>/reject', methods=['POST'])
@login_required
@require_permission('approve_requests')
def reject(id):
    approval = Approval.query.get_or_404(id)
    
    if approval.approver_id != current_user.id:
        flash('Vous n\'êtes pas autorisé à rejeter cette demande', 'danger')
        return redirect(url_for('approvals.show', id=id))
    
    if approval.status != 'pending':
        flash('Cette demande a déjà été traitée', 'warning')
        return redirect(url_for('approvals.show', id=id))
    
    try:
        rejection_reason = request.form.get('rejection_reason', '')
        
        approval.status = 'rejected'
        approval.rejected_at = datetime.utcnow()
        approval.rejection_reason = rejection_reason
        
        notification = Notification(
            user_id=approval.requested_by,
            type='approval_status',
            title='Demande rejetée',
            message=f'Votre demande "{approval.title}" a été rejetée',
            related_entity='approval',
            related_id=approval.id
        )
        db.session.add(notification)
        db.session.commit()
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': True, 'message': 'Demande rejetée'})
        
        flash('Demande rejetée', 'info')
        return redirect(url_for('approvals.show', id=id))
        
    except Exception as e:
        db.session.rollback()
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'message': str(e)}), 400
        flash(f'Erreur: {str(e)}', 'danger')
        return redirect(url_for('approvals.show', id=id))

@approvals_bp.route('/<int:id>/delete', methods=['POST'])
@login_required
def delete(id):
    approval = Approval.query.get_or_404(id)
    
    if approval.requested_by != current_user.id and not current_user.has_permission('manage_approvals'):
        flash('Vous n\'êtes pas autorisé à supprimer cette demande', 'danger')
        return redirect(url_for('approvals.index'))
    
    try:
        db.session.delete(approval)
        db.session.commit()
        flash('Demande supprimée', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erreur: {str(e)}', 'danger')
    
    return redirect(url_for('approvals.index'))

@approvals_bp.route('/stats')
@login_required
@require_permission('view_approvals')
def stats():
    stats = {
        'by_type': {},
        'by_status': {
            'pending': Approval.query.filter_by(status='pending').count(),
            'approved': Approval.query.filter_by(status='approved').count(),
            'rejected': Approval.query.filter_by(status='rejected').count()
        },
        'by_priority': {
            'low': Approval.query.filter_by(priority='low').count(),
            'medium': Approval.query.filter_by(priority='medium').count(),
            'high': Approval.query.filter_by(priority='high').count()
        },
        'recent': Approval.query.order_by(Approval.created_at.desc()).limit(5).all()
    }
    
    types = db.session.query(Approval.request_type, db.func.count(Approval.id)).group_by(Approval.request_type).all()
    stats['by_type'] = {t[0]: t[1] for t in types}
    
    return render_template('approvals/stats.html', stats=stats)


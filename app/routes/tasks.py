from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_required, current_user
from app import db
from app.models import Task, User, Pharmacy
from app.decorators import require_permission
from datetime import datetime

tasks_bp = Blueprint('tasks', __name__, url_prefix='/tasks')

@tasks_bp.route('/quick-create', methods=['POST'])
@login_required
def quick_create():
    """Créer une tâche rapide via modal"""
    try:
        data = request.get_json()
        
        title = data.get('title')
        description = data.get('description', '')
        assigned_to = data.get('assigned_to')
        priority = data.get('priority', 'medium')
        due_date_str = data.get('due_date')
        
        if not title:
            return jsonify({'success': False, 'message': 'Le titre est requis'}), 400
        
        due_date = None
        if due_date_str:
            try:
                due_date = datetime.strptime(due_date_str, '%Y-%m-%d')
            except:
                pass
        
        primary_pharmacy = current_user.get_primary_pharmacy()
        
        task = Task(
            title=title,
            description=description,
            assigned_to=int(assigned_to) if assigned_to else None,
            assigned_by=current_user.id,
            pharmacy_id=primary_pharmacy.id if primary_pharmacy else None,
            priority=priority,
            due_date=due_date,
            status='pending'
        )
        
        db.session.add(task)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Tâche "{title}" créée avec succès',
            'task_id': task.id
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@tasks_bp.route('/')
@login_required
@require_permission('view_tasks')
def index():
    status_filter = request.args.get('status', 'all')
    priority_filter = request.args.get('priority', 'all')
    user_filter = request.args.get('user', 'all')
    
    query = Task.query
    
    if status_filter != 'all':
        query = query.filter_by(status=status_filter)
    
    if priority_filter != 'all':
        query = query.filter_by(priority=priority_filter)
    
    if user_filter == 'my_tasks':
        query = query.filter_by(assigned_to=current_user.id)
    elif user_filter == 'created_by_me':
        query = query.filter_by(assigned_by=current_user.id)
    
    tasks = query.order_by(Task.created_at.desc()).all()
    
    stats = {
        'total': Task.query.count(),
        'pending': Task.query.filter_by(status='pending').count(),
        'in_progress': Task.query.filter_by(status='in_progress').count(),
        'completed': Task.query.filter_by(status='completed').count(),
        'overdue': len([t for t in Task.query.all() if t.is_overdue])
    }
    
    users = User.query.filter_by(is_active=True).all()
    
    return render_template('tasks/index.html', tasks=tasks, stats=stats, users=users)

@tasks_bp.route('/create', methods=['GET', 'POST'])
@login_required
@require_permission('create_task')
def create():
    if request.method == 'POST':
        try:
            title = request.form.get('title')
            description = request.form.get('description')
            assigned_to = request.form.get('assigned_to')
            priority = request.form.get('priority', 'medium')
            due_date_str = request.form.get('due_date')
            
            if not title:
                flash('Le titre est requis', 'danger')
                return redirect(url_for('tasks.create'))
            
            due_date = None
            if due_date_str:
                due_date = datetime.strptime(due_date_str, '%Y-%m-%d')
            
            primary_pharmacy = current_user.get_primary_pharmacy()
            
            task = Task(
                title=title,
                description=description,
                assigned_to=int(assigned_to) if assigned_to else None,
                assigned_by=current_user.id,
                pharmacy_id=primary_pharmacy.id if primary_pharmacy else None,
                priority=priority,
                due_date=due_date,
                status='pending'
            )
            
            db.session.add(task)
            db.session.commit()
            
            flash(f'Tâche "{title}" créée avec succès', 'success')
            return redirect(url_for('tasks.index'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Erreur lors de la création de la tâche: {str(e)}', 'danger')
            return redirect(url_for('tasks.create'))
    
    users = User.query.filter_by(is_active=True).all()
    return render_template('tasks/create.html', users=users)

@tasks_bp.route('/<int:id>')
@login_required
@require_permission('view_tasks')
def show(id):
    task = Task.query.get_or_404(id)
    return render_template('tasks/show.html', task=task)

@tasks_bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@require_permission('edit_task')
def edit(id):
    task = Task.query.get_or_404(id)
    
    if request.method == 'POST':
        try:
            task.title = request.form.get('title')
            task.description = request.form.get('description')
            task.assigned_to = int(request.form.get('assigned_to')) if request.form.get('assigned_to') else None
            task.priority = request.form.get('priority')
            task.status = request.form.get('status')
            
            due_date_str = request.form.get('due_date')
            if due_date_str:
                task.due_date = datetime.strptime(due_date_str, '%Y-%m-%d')
            
            if task.status == 'completed' and not task.completed_at:
                task.completed_at = datetime.utcnow()
            elif task.status != 'completed':
                task.completed_at = None
            
            db.session.commit()
            flash('Tâche mise à jour avec succès', 'success')
            return redirect(url_for('tasks.show', id=task.id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Erreur: {str(e)}', 'danger')
    
    users = User.query.filter_by(is_active=True).all()
    return render_template('tasks/edit.html', task=task, users=users)

@tasks_bp.route('/<int:id>/delete', methods=['POST'])
@login_required
@require_permission('delete_task')
def delete(id):
    task = Task.query.get_or_404(id)
    
    try:
        db.session.delete(task)
        db.session.commit()
        flash('Tâche supprimée avec succès', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erreur: {str(e)}', 'danger')
    
    return redirect(url_for('tasks.index'))

@tasks_bp.route('/<int:id>/status', methods=['POST'])
@login_required
def update_status(id):
    task = Task.query.get_or_404(id)
    
    try:
        status = request.form.get('status')
        task.status = status
        
        if status == 'completed':
            task.completed_at = datetime.utcnow()
        else:
            task.completed_at = None
        
        db.session.commit()
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': True, 'message': 'Statut mis à jour'})
        
        flash('Statut de la tâche mis à jour', 'success')
        return redirect(url_for('tasks.show', id=task.id))
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 400


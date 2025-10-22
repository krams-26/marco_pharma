from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from app.models import db, EmployeeEvaluation, EvaluationCriteria, Employee, User, Audit
from app.decorators import require_permission
from datetime import datetime
from sqlalchemy import func

evaluation_bp = Blueprint('evaluation', __name__, url_prefix='/evaluation')

CRITERIA_DEFAULTS = [
    {'name': 'Ponctualité', 'max_score': 10},
    {'name': 'Qualité du travail', 'max_score': 10},
    {'name': 'Relations avec collègues', 'max_score': 10},
    {'name': 'Respect des procédures', 'max_score': 10},
    {'name': 'Initiative et autonomie', 'max_score': 10},
]

@evaluation_bp.route('/')
@require_permission('manage_hr')
def index():
    page = request.args.get('page', 1, type=int)
    filter_status = request.args.get('status', '')
    filter_employee = request.args.get('employee_id', '')
    
    query = EmployeeEvaluation.query
    
    if filter_status:
        query = query.filter_by(status=filter_status)
    
    if filter_employee:
        query = query.filter_by(employee_id=filter_employee)
    
    evaluations = query.order_by(EmployeeEvaluation.evaluation_date.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    
    stats = {
        'total': EmployeeEvaluation.query.count(),
        'draft': EmployeeEvaluation.query.filter_by(status='draft').count(),
        'submitted': EmployeeEvaluation.query.filter_by(status='submitted').count(),
        'validated': EmployeeEvaluation.query.filter_by(status='validated').count(),
        'avg_score': db.session.query(func.avg(EmployeeEvaluation.overall_score)).scalar() or 0
    }
    
    employees = Employee.query.filter_by(is_active=True).all()
    
    return render_template('evaluation/index.html', 
                         evaluations=evaluations,
                         stats=stats,
                         employees=employees,
                         filter_status=filter_status,
                         filter_employee=filter_employee)

@evaluation_bp.route('/create/<int:employee_id>', methods=['GET', 'POST'])
@require_permission('manage_hr')
def create(employee_id):
    employee = Employee.query.get_or_404(employee_id)
    
    if request.method == 'POST':
        try:
            evaluation = EmployeeEvaluation(
                employee_id=employee_id,
                evaluator_id=current_user.id,
                evaluation_date=datetime.strptime(request.form.get('evaluation_date'), '%Y-%m-%d').date(),
                period_evaluated=request.form.get('period_evaluated'),
                comments=request.form.get('comments'),
                strengths=request.form.get('strengths'),
                improvements=request.form.get('improvements'),
                future_goals=request.form.get('future_goals'),
                status=request.form.get('status', 'draft')
            )
            
            criteria_names = request.form.getlist('criteria_name[]')
            criteria_scores = request.form.getlist('criteria_score[]')
            criteria_max = request.form.getlist('criteria_max[]')
            
            total_score = 0
            total_max = 0
            
            for i in range(len(criteria_names)):
                if criteria_names[i] and criteria_scores[i]:
                    score = float(criteria_scores[i])
                    max_score = float(criteria_max[i]) if criteria_max[i] else 10.0
                    
                    criterion = EvaluationCriteria(
                        criteria_name=criteria_names[i],
                        score=score,
                        max_score=max_score,
                        notes=request.form.getlist('criteria_notes[]')[i] if i < len(request.form.getlist('criteria_notes[]')) else ''
                    )
                    evaluation.criteria.append(criterion)
                    
                    total_score += score
                    total_max += max_score
            
            evaluation.overall_score = (total_score / total_max * 10) if total_max > 0 else 0
            
            db.session.add(evaluation)
            db.session.flush()
            
            audit = Audit(
                user_id=current_user.id,
                action='create_evaluation',
                entity_type='evaluation',
                entity_id=evaluation.id,
                details=f'Évaluation créée pour {employee.employee_id}',
                ip_address=request.remote_addr
            )
            db.session.add(audit)
            
            db.session.commit()
            
            flash('Évaluation créée avec succès!', 'success')
            return redirect(url_for('evaluation.view', id=evaluation.id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Erreur: {str(e)}', 'danger')
    
    return render_template('evaluation/create.html', employee=employee, criteria_defaults=CRITERIA_DEFAULTS)

@evaluation_bp.route('/view/<int:id>')
@require_permission('manage_hr')
def view(id):
    evaluation = EmployeeEvaluation.query.get_or_404(id)
    return render_template('evaluation/view.html', evaluation=evaluation)

@evaluation_bp.route('/edit/<int:id>', methods=['GET', 'POST'])
@require_permission('manage_hr')
def edit(id):
    evaluation = EmployeeEvaluation.query.get_or_404(id)
    
    if request.method == 'POST':
        try:
            evaluation.evaluation_date = datetime.strptime(request.form.get('evaluation_date'), '%Y-%m-%d').date()
            evaluation.period_evaluated = request.form.get('period_evaluated')
            evaluation.comments = request.form.get('comments')
            evaluation.strengths = request.form.get('strengths')
            evaluation.improvements = request.form.get('improvements')
            evaluation.future_goals = request.form.get('future_goals')
            evaluation.status = request.form.get('status', 'draft')
            
            EvaluationCriteria.query.filter_by(evaluation_id=id).delete()
            
            criteria_names = request.form.getlist('criteria_name[]')
            criteria_scores = request.form.getlist('criteria_score[]')
            criteria_max = request.form.getlist('criteria_max[]')
            
            total_score = 0
            total_max = 0
            
            for i in range(len(criteria_names)):
                if criteria_names[i] and criteria_scores[i]:
                    score = float(criteria_scores[i])
                    max_score = float(criteria_max[i]) if criteria_max[i] else 10.0
                    
                    criterion = EvaluationCriteria(
                        evaluation_id=evaluation.id,
                        criteria_name=criteria_names[i],
                        score=score,
                        max_score=max_score
                    )
                    db.session.add(criterion)
                    
                    total_score += score
                    total_max += max_score
            
            evaluation.overall_score = (total_score / total_max * 10) if total_max > 0 else 0
            
            db.session.commit()
            
            flash('Évaluation modifiée avec succès!', 'success')
            return redirect(url_for('evaluation.view', id=evaluation.id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Erreur: {str(e)}', 'danger')
    
    return render_template('evaluation/edit.html', evaluation=evaluation)

@evaluation_bp.route('/dashboard')
@require_permission('manage_hr')
def dashboard():
    evaluations_count = EmployeeEvaluation.query.count()
    avg_score = db.session.query(func.avg(EmployeeEvaluation.overall_score)).scalar() or 0
    
    recent_evaluations = EmployeeEvaluation.query.order_by(EmployeeEvaluation.evaluation_date.desc()).limit(10).all()
    
    employee_scores = db.session.query(
        Employee.employee_id,
        Employee.position,
        func.avg(EmployeeEvaluation.overall_score).label('avg_score'),
        func.count(EmployeeEvaluation.id).label('eval_count')
    ).join(EmployeeEvaluation).group_by(Employee.id).all()
    
    return render_template('evaluation/dashboard.html',
                         evaluations_count=evaluations_count,
                         avg_score=avg_score,
                         recent_evaluations=recent_evaluations,
                         employee_scores=employee_scores)


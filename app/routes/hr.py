from flask import Blueprint, render_template, request, flash, redirect, url_for
from app.decorators import require_permission
from flask_login import login_required, current_user
from app.models import db, Employee, Absence, SalaryPayment, LeaveRequest, CreditRequest, User, Audit
from datetime import datetime

hr_bp = Blueprint('hr', __name__, url_prefix='/hr')

@hr_bp.route('/')
@require_permission('manage_hr')
def index():
    employees = Employee.query.filter_by(is_active=True).all()
    return render_template('hr/index.html', employees=employees)

@hr_bp.route('/absences')
@require_permission('manage_hr')
def absences():
    page = request.args.get('page', 1, type=int)
    absences = Absence.query.order_by(Absence.absence_date.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    return render_template('hr/absences.html', absences=absences)

@hr_bp.route('/add-absence', methods=['GET', 'POST'])
@require_permission('manage_hr')
def add_absence():
    if request.method == 'POST':
        try:
            absence = Absence(
                employee_id=request.form.get('employee_id'),
                absence_date=datetime.strptime(request.form.get('absence_date'), '%Y-%m-%d').date(),
                reason=request.form.get('reason'),
                notes=request.form.get('notes')
            )
            
            db.session.add(absence)
            db.session.commit()
            
            flash('Absence enregistrée avec succès!', 'success')
            return redirect(url_for('hr.absences'))
        except Exception as e:
            db.session.rollback()
            flash(f'Erreur: {str(e)}', 'danger')
    
    employees = Employee.query.filter_by(is_active=True).all()
    return render_template('hr/add_absence.html', employees=employees)

@hr_bp.route('/salaries')
@login_required
def salaries():
    page = request.args.get('page', 1, type=int)
    payments = SalaryPayment.query.order_by(SalaryPayment.payment_date.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    return render_template('hr/salaries.html', payments=payments)

@hr_bp.route('/pay-salary', methods=['GET', 'POST'])
@login_required
def pay_salary():
    if request.method == 'POST':
        try:
            payment = SalaryPayment(
                employee_id=request.form.get('employee_id'),
                amount=float(request.form.get('amount')),
                period=request.form.get('period'),
                payment_date=datetime.strptime(request.form.get('payment_date'), '%Y-%m-%d').date(),
                payment_method=request.form.get('payment_method'),
                notes=request.form.get('notes')
            )
            
            db.session.add(payment)
            db.session.commit()
            
            flash('Paiement enregistré avec succès!', 'success')
            return redirect(url_for('hr.salaries'))
        except Exception as e:
            db.session.rollback()
            flash(f'Erreur: {str(e)}', 'danger')
    
    employees = Employee.query.filter_by(is_active=True).all()
    return render_template('hr/pay_salary.html', employees=employees)

@hr_bp.route('/leave-requests')
@login_required
def leave_requests():
    page = request.args.get('page', 1, type=int)
    requests = LeaveRequest.query.order_by(LeaveRequest.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    return render_template('hr/leave_requests.html', requests=requests)

@hr_bp.route('/add-leave-request', methods=['GET', 'POST'])
@login_required
def add_leave_request():
    if request.method == 'POST':
        try:
            leave_request = LeaveRequest(
                employee_id=request.form.get('employee_id'),
                start_date=datetime.strptime(request.form.get('start_date'), '%Y-%m-%d').date(),
                end_date=datetime.strptime(request.form.get('end_date'), '%Y-%m-%d').date(),
                leave_type=request.form.get('leave_type'),
                reason=request.form.get('reason'),
                status='pending'
            )
            
            db.session.add(leave_request)
            db.session.commit()
            
            flash('Demande de congé enregistrée avec succès!', 'success')
            return redirect(url_for('hr.leave_requests'))
        except Exception as e:
            db.session.rollback()
            flash(f'Erreur: {str(e)}', 'danger')
    
    employees = Employee.query.filter_by(is_active=True).all()
    return render_template('hr/add_leave_request.html', employees=employees)

@hr_bp.route('/approve-leave/<int:id>', methods=['POST'])
@login_required
def approve_leave(id):
    leave_request = LeaveRequest.query.get_or_404(id)
    leave_request.status = 'approved'
    db.session.commit()
    flash('Demande de congé approuvée!', 'success')
    return redirect(url_for('hr.leave_requests'))

@hr_bp.route('/reject-leave/<int:id>', methods=['POST'])
@login_required
def reject_leave(id):
    leave_request = LeaveRequest.query.get_or_404(id)
    leave_request.status = 'rejected'
    db.session.commit()
    flash('Demande de congé rejetée!', 'info')
    return redirect(url_for('hr.leave_requests'))

@hr_bp.route('/credit-requests')
@login_required
def credit_requests():
    page = request.args.get('page', 1, type=int)
    requests = CreditRequest.query.order_by(CreditRequest.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    return render_template('hr/credit_requests.html', requests=requests)

@hr_bp.route('/add-credit-request', methods=['GET', 'POST'])
@login_required
def add_credit_request():
    if request.method == 'POST':
        try:
            credit_request = CreditRequest(
                employee_id=request.form.get('employee_id'),
                amount=float(request.form.get('amount')),
                reason=request.form.get('reason'),
                status='pending'
            )
            
            db.session.add(credit_request)
            db.session.commit()
            
            flash('Demande de crédit enregistrée avec succès!', 'success')
            return redirect(url_for('hr.credit_requests'))
        except Exception as e:
            db.session.rollback()
            flash(f'Erreur: {str(e)}', 'danger')
    
    employees = Employee.query.filter_by(is_active=True).all()
    return render_template('hr/add_credit_request.html', employees=employees)

@hr_bp.route('/approve-credit/<int:id>', methods=['POST'])
@login_required
def approve_credit(id):
    credit_request = CreditRequest.query.get_or_404(id)
    credit_request.status = 'approved'
    db.session.commit()
    flash('Demande de crédit approuvée!', 'success')
    return redirect(url_for('hr.credit_requests'))

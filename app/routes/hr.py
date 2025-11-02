from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from app.decorators import require_permission
from flask_login import login_required, current_user
from app.models import db, Employee, Absence, SalaryPayment, LeaveRequest, CreditRequest, User, Audit, ExchangeRate
from datetime import datetime, date
from app.pharmacy_utils import filter_by_pharmacy, get_accessible_pharmacies, is_admin
from app.export_utils import export_to_csv, export_to_excel

hr_bp = Blueprint('hr', __name__, url_prefix='/hr')

def get_accessible_employees():
    """Récupérer tous les employés actifs du système
    
    Chaque utilisateur est d'office un employé/personnel.
    On récupère donc tous les utilisateurs actifs du système.
    Optimisé pour éviter les requêtes N+1.
    """
    # Récupérer tous les utilisateurs actifs avec gestion des None pour order_by
    from sqlalchemy import or_
    users = User.query.filter_by(is_active=True).order_by(
        User.first_name.nullslast(), 
        User.last_name.nullslast(),
        User.username
    ).all()
    
    # Récupérer tous les employés en une seule requête (optimisation N+1)
    user_ids = [user.id for user in users]
    existing_employees = {}
    if user_ids:
        employees = Employee.query.filter(Employee.user_id.in_(user_ids)).all()
        for emp in employees:
            existing_employees[emp.user_id] = emp
    
    employees_list = []
    for user in users:
        # Chercher si un Employee existe déjà pour cet utilisateur
        employee = existing_employees.get(user.id)
        
        if not employee:
            # Créer un Employee virtuel pour l'affichage
            employee = _create_virtual_employee(user)
        elif not employee.is_active:
            # Passer les employés inactifs (mais l'utilisateur est actif, donc on crée un virtuel)
            employee = _create_virtual_employee(user)
            
        employees_list.append(employee)
    
    return employees_list

def _create_virtual_employee(user_obj):
    """Créer un Employee virtuel à partir d'un User"""
    class VirtualEmployee:
        def __init__(self, user):
            self.id = user.id  # Utiliser user_id comme ID temporaire
            self.user_id = user.id
            self.user = user
            self.employee_id = f"EMP{user.id:04d}"
            self.position = getattr(user, 'position', user.role) if hasattr(user, 'role') else 'Employé'
            self.department = None
            self.salary = 0.0
            self.hire_date = user.created_at.date() if user.created_at else None
            self.is_active = user.is_active
            self.created_at = user.created_at
        
        @property
        def first_name(self):
            return self.user.first_name if self.user else ''
        
        @property
        def last_name(self):
            return self.user.last_name if self.user else ''
        
        @property
        def full_name(self):
            name = f"{self.first_name} {self.last_name}".strip()
            if not name:
                return self.user.username if self.user else 'N/A'
            return name
    
    return VirtualEmployee(user_obj)

# ========== ROUTES API POUR MODALS ==========

@hr_bp.route('/quick-add-absence', methods=['POST'])
@login_required
def quick_add_absence():
    """Enregistrer une absence via modal"""
    try:
        data = request.get_json()
        
        employee_id_or_user_id = data.get('employee_id')
        absence_date_str = data.get('absence_date')
        reason = data.get('reason')
        is_justified = data.get('is_justified', False)
        notes = data.get('notes', '')
        
        if not employee_id_or_user_id or not absence_date_str:
            return jsonify({'success': False, 'message': 'Employé et date requis'}), 400
        
        # Vérifier si c'est un ID d'employé ou d'utilisateur avec gestion d'erreur
        try:
            employee_id_int = int(employee_id_or_user_id)
        except (ValueError, TypeError):
            return jsonify({'success': False, 'message': 'ID employé invalide'}), 400
        
        # D'abord, vérifier si c'est un ID d'employé existant
        employee = Employee.query.get(employee_id_int)
        
        if not employee:
            # Ce n'est pas un employee_id, donc c'est probablement un user_id
            employee = Employee.query.filter_by(user_id=employee_id_int).first()
            
        if not employee:
            # Si pas d'employé, créer un enregistrement Employee pour cet utilisateur
            user = User.query.get(employee_id_int)
            if not user:
                return jsonify({'success': False, 'message': 'Utilisateur introuvable'}), 404
            
            # Créer l'employé automatiquement
            employee = Employee(
                user_id=user.id,
                employee_id=f"EMP{user.id:04d}",
                position=user.role,
                is_active=user.is_active
            )
            db.session.add(employee)
            db.session.flush()
        
        absence = Absence(
            employee_id=employee.id,
            absence_date=datetime.strptime(absence_date_str, '%Y-%m-%d').date(),
            reason=reason,
            is_justified=is_justified,
            notes=notes
        )
        
        db.session.add(absence)
        
        # Audit
        employee_name = employee.user.full_name if employee.user else f"Employé {employee.id}"
        audit = Audit(
            user_id=current_user.id,
            action='create_absence',
            entity_type='absence',
            entity_id=absence.id,
            details=f'Absence enregistrée pour {employee_name}',
            ip_address=request.remote_addr
        )
        db.session.add(audit)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Absence enregistrée avec succès'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@hr_bp.route('/quick-add-leave', methods=['POST'])
@login_required
def quick_add_leave():
    """Créer une demande de congé via modal"""
    try:
        data = request.get_json()
        
        employee_id_or_user_id = data.get('employee_id')
        leave_type = data.get('leave_type')
        start_date_str = data.get('start_date')
        end_date_str = data.get('end_date')
        reason = data.get('reason', '')
        
        if not employee_id_or_user_id or not start_date_str or not end_date_str:
            return jsonify({'success': False, 'message': 'Données incomplètes'}), 400
        
        # Vérifier si c'est un ID d'employé ou d'utilisateur avec gestion d'erreur
        try:
            employee_id_int = int(employee_id_or_user_id)
        except (ValueError, TypeError):
            return jsonify({'success': False, 'message': 'ID employé invalide'}), 400
        
        employee = Employee.query.filter_by(user_id=employee_id_int).first()
        if not employee:
            # Si pas d'employé, créer un enregistrement Employee pour cet utilisateur
            user = User.query.get(employee_id_int)
            if not user:
                return jsonify({'success': False, 'message': 'Utilisateur introuvable'}), 404
            
            employee = Employee(
                user_id=user.id,
                employee_id=f"EMP{user.id:04d}",
                position=user.role,
                is_active=user.is_active
            )
            db.session.add(employee)
            db.session.flush()
        
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        
        if end_date < start_date:
            return jsonify({'success': False, 'message': 'La date de fin doit être après la date de début'}), 400
        
        duration = (end_date - start_date).days + 1
        
        leave_request = LeaveRequest(
            employee_id=employee.id,
            leave_type=leave_type,
            start_date=start_date,
            end_date=end_date,
            duration=duration,
            reason=reason,
            status='pending'
        )
        
        db.session.add(leave_request)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Demande de congé créée ({duration} jours)'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@hr_bp.route('/quick-pay-salary', methods=['POST'])
@login_required
def quick_pay_salary():
    """Enregistrer un paiement de salaire via modal"""
    try:
        data = request.get_json()
        
        employee_id_or_user_id = data.get('employee_id')
        amount = float(data.get('amount', 0))
        period = data.get('period')
        payment_method = data.get('payment_method', 'cash')
        payment_date_str = data.get('payment_date')
        notes = data.get('notes', '')
        
        if not employee_id_or_user_id or amount <= 0 or not period:
            return jsonify({'success': False, 'message': 'Données incomplètes'}), 400
        
        # Vérifier si c'est un ID d'employé ou d'utilisateur avec gestion d'erreur
        try:
            employee_id_int = int(employee_id_or_user_id)
        except (ValueError, TypeError):
            return jsonify({'success': False, 'message': 'ID employé invalide'}), 400
        
        employee = Employee.query.filter_by(user_id=employee_id_int).first()
        if not employee:
            # Si pas d'employé, créer un enregistrement Employee pour cet utilisateur
            user = User.query.get(employee_id_int)
            if not user:
                return jsonify({'success': False, 'message': 'Utilisateur introuvable'}), 404
            
            employee = Employee(
                user_id=user.id,
                employee_id=f"EMP{user.id:04d}",
                position=user.role,
                is_active=user.is_active
            )
            db.session.add(employee)
            db.session.flush()
        
        payment_date = datetime.strptime(payment_date_str, '%Y-%m-%d').date() if payment_date_str else date.today()
        
        payment = SalaryPayment(
            employee_id=employee.id,
            amount=amount,
            period=period,
            payment_date=payment_date,
            payment_method=payment_method,
            notes=notes
        )
        
        db.session.add(payment)
        
        # Audit
        employee_name = employee.user.full_name if employee.user else f"Employé {employee.id}"
        audit = Audit(
            user_id=current_user.id,
            action='pay_salary',
            entity_type='salary_payment',
            entity_id=payment.id,
            details=f'Salaire payé: {employee_name} - ${amount:.2f}',
            ip_address=request.remote_addr
        )
        db.session.add(audit)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Paiement enregistré avec succès'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@hr_bp.route('/quick-add-credit', methods=['POST'])
@login_required
def quick_add_credit():
    """Créer une demande d'avance via modal"""
    try:
        data = request.get_json()
        
        employee_id_or_user_id = data.get('employee_id')
        amount = float(data.get('amount', 0))
        reason = data.get('reason', '')
        
        if not employee_id_or_user_id or amount <= 0:
            return jsonify({'success': False, 'message': 'Données incomplètes'}), 400
        
        # Vérifier si c'est un ID d'employé ou d'utilisateur avec gestion d'erreur
        try:
            employee_id_int = int(employee_id_or_user_id)
        except (ValueError, TypeError):
            return jsonify({'success': False, 'message': 'ID employé invalide'}), 400
        
        employee = Employee.query.filter_by(user_id=employee_id_int).first()
        if not employee:
            # Si pas d'employé, créer un enregistrement Employee pour cet utilisateur
            user = User.query.get(employee_id_int)
            if not user:
                return jsonify({'success': False, 'message': 'Utilisateur introuvable'}), 404
            
            employee = Employee(
                user_id=user.id,
                employee_id=f"EMP{user.id:04d}",
                position=user.role,
                is_active=user.is_active
            )
            db.session.add(employee)
            db.session.flush()
        
        credit_request = CreditRequest(
            employee_id=employee.id,
            amount=amount,
            reason=reason,
            status='pending',
            request_date=date.today()
        )
        
        db.session.add(credit_request)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Demande d\'avance créée avec succès'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

# ========== ROUTES NORMALES ==========

@hr_bp.route('/')
@require_permission('manage_hr')
def index():
    employees = get_accessible_employees()
    return render_template('hr/index.html', employees=employees)

@hr_bp.route('/absences')
@require_permission('manage_hr')
def absences():
    page = request.args.get('page', 1, type=int)
    absences_query = Absence.query.order_by(Absence.absence_date.desc())
    
    # Filtrer les absences selon le scope (optionnel selon les besoins)
    # Pour l'instant, on montre toutes les absences de tous les employés
    # car chaque employé est un utilisateur du système
    
    absences = absences_query.paginate(page=page, per_page=6, error_out=False)
    employees = get_accessible_employees()
    return render_template('hr/absences.html', absences=absences, employees=employees)

@hr_bp.route('/add-absence', methods=['GET', 'POST'])
@require_permission('manage_hr')
def add_absence():
    if request.method == 'POST':
        try:
            employee_id_str = request.form.get('employee_id')
            if not employee_id_str:
                flash('Employé requis', 'danger')
                return redirect(url_for('hr.add_absence'))
            
            try:
                employee_id_or_user_id = int(employee_id_str)
            except (ValueError, TypeError):
                flash('ID employé invalide', 'danger')
                return redirect(url_for('hr.add_absence'))
            
            # D'abord, vérifier si c'est un ID d'employé existant
            employee = Employee.query.get(employee_id_or_user_id)
            
            if not employee:
                # Ce n'est pas un employee_id, donc c'est probablement un user_id
                employee = Employee.query.filter_by(user_id=employee_id_or_user_id).first()
            
            if not employee:
                # Si pas d'employé, créer un enregistrement Employee pour cet utilisateur
                user = User.query.get(employee_id_or_user_id)
                if not user:
                    flash('Utilisateur introuvable', 'danger')
                    return redirect(url_for('hr.add_absence'))
                
                employee = Employee(
                    user_id=user.id,
                    employee_id=f"EMP{user.id:04d}",
                    position=user.role,
                    is_active=user.is_active
                )
                db.session.add(employee)
                db.session.flush()
            
            absence = Absence(
                employee_id=employee.id,
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
    
    employees = get_accessible_employees()
    return render_template('hr/add_absence.html', employees=employees)

@hr_bp.route('/salaries')
@login_required
def salaries():
    page = request.args.get('page', 1, type=int)
    payments_query = SalaryPayment.query.order_by(SalaryPayment.payment_date.desc())
    
    # Filtrer les paiements selon le scope (optionnel selon les besoins)
    # Pour l'instant, on montre tous les paiements de tous les employés
    # car chaque employé est un utilisateur du système
    
    payments = payments_query.paginate(page=page, per_page=6, error_out=False)
    employees = get_accessible_employees()
    # Taux de change pour affichage équivalents
    exchange_rate = ExchangeRate.query.filter_by(from_currency='USD', to_currency='CDF').first()
    rate = exchange_rate.rate if exchange_rate else 2800
    return render_template('hr/salaries.html', payments=payments, employees=employees, exchange_rate=rate)

@hr_bp.route('/pay-salary', methods=['GET', 'POST'])
@login_required
def pay_salary():
    if request.method == 'POST':
        try:
            employee_id_str = request.form.get('employee_id')
            if not employee_id_str:
                flash('Employé requis', 'danger')
                return redirect(url_for('hr.pay_salary'))
            
            try:
                employee_id_or_user_id = int(employee_id_str)
            except (ValueError, TypeError):
                flash('ID employé invalide', 'danger')
                return redirect(url_for('hr.pay_salary'))
            
            # Vérifier si c'est un ID d'employé ou d'utilisateur
            employee = Employee.query.filter_by(user_id=employee_id_or_user_id).first()
            if not employee:
                # Si pas d'employé, créer un enregistrement Employee pour cet utilisateur
                user = User.query.get(employee_id_or_user_id)
                if not user:
                    flash('Utilisateur introuvable', 'danger')
                    return redirect(url_for('hr.pay_salary'))
                
                employee = Employee(
                    user_id=user.id,
                    employee_id=f"EMP{user.id:04d}",
                    position=user.role,
                    is_active=user.is_active
                )
                db.session.add(employee)
                db.session.flush()
            
            payment = SalaryPayment(
                employee_id=employee.id,
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
    
    employees = get_accessible_employees()
    current_period = datetime.now().strftime('%Y-%m')
    today = datetime.now().strftime('%Y-%m-%d')
    # Taux de change pour équivalents
    exchange_rate = ExchangeRate.query.filter_by(from_currency='USD', to_currency='CDF').first()
    rate = exchange_rate.rate if exchange_rate else 2800
    return render_template('hr/pay_salary.html', employees=employees, current_period=current_period, today=today, exchange_rate=rate)

@hr_bp.route('/leave-requests')
@login_required
def leave_requests():
    page = request.args.get('page', 1, type=int)
    requests_query = LeaveRequest.query.order_by(LeaveRequest.created_at.desc())
    
    # Filtrer les demandes selon le scope (optionnel selon les besoins)
    # Pour l'instant, on montre toutes les demandes de tous les employés
    # car chaque employé est un utilisateur du système
    
    requests = requests_query.paginate(page=page, per_page=6, error_out=False)
    employees = get_accessible_employees()
    return render_template('hr/leave_requests.html', requests=requests, employees=employees)

@hr_bp.route('/add-leave-request', methods=['GET', 'POST'])
@login_required
def add_leave_request():
    if request.method == 'POST':
        try:
            employee_id_str = request.form.get('employee_id')
            if not employee_id_str:
                flash('Employé requis', 'danger')
                return redirect(url_for('hr.add_leave_request'))
            
            try:
                employee_id_or_user_id = int(employee_id_str)
            except (ValueError, TypeError):
                flash('ID employé invalide', 'danger')
                return redirect(url_for('hr.add_leave_request'))
            
            # Vérifier si c'est un ID d'employé ou d'utilisateur
            employee = Employee.query.filter_by(user_id=employee_id_or_user_id).first()
            if not employee:
                # Si pas d'employé, créer un enregistrement Employee pour cet utilisateur
                user = User.query.get(employee_id_or_user_id)
                if not user:
                    flash('Utilisateur introuvable', 'danger')
                    return redirect(url_for('hr.add_leave_request'))
                
                employee = Employee(
                    user_id=user.id,
                    employee_id=f"EMP{user.id:04d}",
                    position=user.role,
                    is_active=user.is_active
                )
                db.session.add(employee)
                db.session.flush()
            
            leave_request = LeaveRequest(
                employee_id=employee.id,
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
    
    employees = get_accessible_employees()
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
    requests_query = CreditRequest.query.order_by(CreditRequest.created_at.desc())
    
    # Filtrer les demandes selon le scope (optionnel selon les besoins)
    # Pour l'instant, on montre toutes les demandes de tous les employés
    # car chaque employé est un utilisateur du système
    
    requests = requests_query.paginate(page=page, per_page=6, error_out=False)
    employees = get_accessible_employees()
    # Taux de change pour équivalents
    exchange_rate = ExchangeRate.query.filter_by(from_currency='USD', to_currency='CDF').first()
    rate = exchange_rate.rate if exchange_rate else 2800
    return render_template('hr/credit_requests.html', requests=requests, employees=employees, exchange_rate=rate)

@hr_bp.route('/add-credit-request', methods=['GET', 'POST'])
@login_required
def add_credit_request():
    if request.method == 'POST':
        try:
            employee_id_str = request.form.get('employee_id')
            if not employee_id_str:
                flash('Employé requis', 'danger')
                return redirect(url_for('hr.add_credit_request'))
            
            try:
                employee_id_or_user_id = int(employee_id_str)
            except (ValueError, TypeError):
                flash('ID employé invalide', 'danger')
                return redirect(url_for('hr.add_credit_request'))
            
            # Vérifier si c'est un ID d'employé ou d'utilisateur
            employee = Employee.query.filter_by(user_id=employee_id_or_user_id).first()
            if not employee:
                # Si pas d'employé, créer un enregistrement Employee pour cet utilisateur
                user = User.query.get(employee_id_or_user_id)
                if not user:
                    flash('Utilisateur introuvable', 'danger')
                    return redirect(url_for('hr.add_credit_request'))
                
                employee = Employee(
                    user_id=user.id,
                    employee_id=f"EMP{user.id:04d}",
                    position=user.role,
                    is_active=user.is_active
                )
                db.session.add(employee)
                db.session.flush()
            
            credit_request = CreditRequest(
                employee_id=employee.id,
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
    
    employees = get_accessible_employees()
    return render_template('hr/add_credit_request.html', employees=employees)

@hr_bp.route('/approve-credit/<int:id>', methods=['POST'])
@login_required
def approve_credit(id):
    credit_request = CreditRequest.query.get_or_404(id)
    credit_request.status = 'approved'
    db.session.commit()
    flash('Demande de crédit approuvée!', 'success')
    return redirect(url_for('hr.credit_requests'))

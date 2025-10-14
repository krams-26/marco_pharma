from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from app.models import db, User, Audit

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/')
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        remember = request.form.get('remember', False)
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            if user.is_active:
                login_user(user, remember=remember)
                
                audit = Audit(
                    user_id=user.id,
                    action='login',
                    entity_type='user',
                    entity_id=user.id,
                    details=f'Connexion réussie de {user.username}',
                    ip_address=request.remote_addr
                )
                db.session.add(audit)
                db.session.commit()
                
                next_page = request.args.get('next')
                return redirect(next_page or url_for('dashboard.index'))
            else:
                flash('Votre compte est désactivé.', 'danger')
        else:
            flash('Nom d\'utilisateur ou mot de passe incorrect.', 'danger')
    
    return render_template('auth/login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    audit = Audit(
        user_id=current_user.id,
        action='logout',
        entity_type='user',
        entity_id=current_user.id,
        details=f'Déconnexion de {current_user.username}',
        ip_address=request.remote_addr
    )
    db.session.add(audit)
    db.session.commit()
    
    logout_user()
    flash('Vous avez été déconnecté avec succès.', 'info')
    return redirect(url_for('auth.login'))

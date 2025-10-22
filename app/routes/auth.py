from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from app.models import db, User
from app.helpers import ActivityLogger

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/', methods=['GET', 'POST'])
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
                
                # Logger la connexion réussie
                ActivityLogger.log_login(
                    user_id=user.id,
                    username=user.username,
                    result='success',
                    details=f'Connexion réussie: {user.username} ({user.role})'
                )
                
                next_page = request.args.get('next')
                return redirect(next_page or url_for('dashboard.index'))
            else:
                # Logger la tentative sur compte désactivé
                ActivityLogger.log_login(
                    user_id=user.id if user else None,
                    username=username,
                    result='denied',
                    details=f'Tentative de connexion sur compte désactivé: {username}'
                )
                flash('Votre compte est désactivé. Contactez l\'administrateur.', 'danger')
        else:
            # Logger l'échec de connexion
            ActivityLogger.log_login(
                user_id=user.id if user else None,
                username=username,
                result='failed',
                details=f'Échec de connexion: identifiants incorrects pour {username}'
            )
            flash('Nom d\'utilisateur ou mot de passe incorrect.', 'danger')
    
    return render_template('auth/login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    # Logger la déconnexion
    ActivityLogger.log_logout(
        user_id=current_user.id,
        username=current_user.username
    )
    
    logout_user()
    flash('Vous avez été déconnecté avec succès.', 'info')
    return redirect(url_for('auth.login'))

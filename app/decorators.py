from functools import wraps
from flask import flash, redirect, url_for, render_template, abort
from flask_login import current_user

def require_permission(permission):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                flash('Veuillez vous connecter pour accéder à cette page.', 'danger')
                return redirect(url_for('auth.login'))
            
            if not current_user.has_permission(permission):
                return render_template('errors/403.html', permission=permission), 403
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

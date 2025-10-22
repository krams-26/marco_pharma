from flask import Flask
from flask_login import LoginManager
from flask_migrate import Migrate
from app.models import db, User
from app.config import Config
from datetime import datetime

migrate = Migrate()
login_manager = LoginManager()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Veuillez vous connecter pour accéder à cette page.'
    
    @app.template_filter('format_datetime')
    def format_datetime(value, format='%d/%m/%Y %H:%M'):
        if value == 'now':
            value = datetime.now()
        if isinstance(value, str):
            return value
        if value is None:
            return ''
        return value.strftime(format)
    
    @app.template_filter('usd_to_cdf')
    def usd_to_cdf(amount_usd):
        """Convertir USD en CDF selon le taux de change actuel"""
        from app.models import ExchangeRate
        if amount_usd is None:
            return 0
        amount_usd = float(amount_usd)
        
        # Récupérer le taux USD -> CDF
        rate = ExchangeRate.query.filter_by(
            from_currency='USD',
            to_currency='CDF'
        ).first()
        
        if rate:
            return amount_usd * rate.rate
        # Taux par défaut si non configuré
        return amount_usd * 2800
    
    @app.template_filter('format_price_dual')
    def format_price_dual(amount_usd):
        """Formater le prix en USD avec équivalent CDF en petit"""
        if amount_usd is None:
            return '$0.00<br><small class="text-muted">0 FC</small>'
        amount_usd = float(amount_usd)
        amount_cdf = usd_to_cdf(amount_usd)
        return f'${amount_usd:,.2f}<br><small class="text-muted">{amount_cdf:,.0f} FC</small>'
    
    @app.template_filter('format_number')
    def format_number(value):
        """Formater un nombre avec des séparateurs de milliers"""
        if value is None:
            return '0'
        try:
            return f'{float(value):,.0f}'
        except (ValueError, TypeError):
            return str(value)
    
    @app.context_processor
    def utility_processor():
        """Fonctions utilitaires disponibles dans tous les templates"""
        def has_any_permission(*permissions):
            """Vérifie si l'utilisateur a au moins une des permissions listées"""
            from flask_login import current_user
            if not current_user.is_authenticated:
                return False
            for perm in permissions:
                if current_user.has_permission(perm):
                    return True
            return False
        
        # Fournir la liste des utilisateurs actifs pour les modals
        from flask_login import current_user
        from app.models import User
        all_users = []
        if current_user.is_authenticated and current_user.role in ['admin', 'manager']:
            all_users = User.query.filter_by(is_active=True).order_by(User.first_name).all()
        
        return dict(has_any_permission=has_any_permission, all_users=all_users)
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    from app.routes.auth import auth_bp
    from app.routes.dashboard import dashboard_bp
    from app.routes.pos import pos_bp
    from app.routes.products import products_bp
    from app.routes.customers import customers_bp
    from app.routes.sales import sales_bp
    from app.routes.users import users_bp
    from app.routes.stock import stock_bp
    from app.routes.hr import hr_bp
    from app.routes.payments import payments_bp
    from app.routes.cashier import cashier_bp
    from app.routes.reports import reports_bp
    from app.routes.audits import audits_bp
    from app.routes.settings import settings_bp
    from app.routes.proforma import proforma_bp
    from app.routes.pharmacies import pharmacies_bp
    from app.routes.notifications import notifications_bp
    from app.routes.credit_sales import credit_sales_bp
    from app.routes.validation import validation_bp
    from app.routes.evaluation import evaluation_bp
    from app.routes.tasks import tasks_bp
    from app.routes.approvals import approvals_bp
    from app.routes.suppliers import suppliers_bp
    from app.routes.api_modals import api_modals_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(pos_bp)
    app.register_blueprint(products_bp)
    app.register_blueprint(customers_bp)
    app.register_blueprint(sales_bp)
    app.register_blueprint(users_bp)
    app.register_blueprint(stock_bp)
    app.register_blueprint(hr_bp)
    app.register_blueprint(payments_bp)
    app.register_blueprint(cashier_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(audits_bp)
    app.register_blueprint(settings_bp)
    app.register_blueprint(proforma_bp)
    app.register_blueprint(pharmacies_bp)
    app.register_blueprint(notifications_bp)
    app.register_blueprint(credit_sales_bp)
    app.register_blueprint(validation_bp)
    app.register_blueprint(evaluation_bp)
    app.register_blueprint(tasks_bp)
    app.register_blueprint(approvals_bp)
    app.register_blueprint(suppliers_bp)
    app.register_blueprint(api_modals_bp)
    
    with app.app_context():
        db.create_all()
        
        from app.models import User, Setting, Pharmacy, UserPharmacy
        
        if not Pharmacy.query.first():
            default_pharmacy = Pharmacy(
                name='Pharmacie MARCOPHAR Centrale',
                type='depot',
                code='DEPOT-CENTRAL-001',
                address='Adresse principale',
                phone='+243 XXX XXX XXX',
                email='central@marcophar.com',
                manager_name='Gestionnaire Principal',
                status='active',
                is_active=True,
                revenue_target=50000.0
            )
            db.session.add(default_pharmacy)
            db.session.commit()
        
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            admin = User(
                username='admin',
                email='admin@pharmacy.com',
                first_name='Admin',
                last_name='System',
                role='admin',
                is_active=True
            )
            admin.set_password('admin123')
            
            default_perms = {
                'view_dashboard': True,
                'manage_products': True,
                'manage_sales': True,
                'manage_customers': True,
                'manage_users': True,
                'manage_stock': True,
                'manage_hr': True,
                'manage_payments': True,
                'manage_cashier': True,
                'view_reports': True,
                'view_audits': True,
                'manage_settings': True
            }
            admin.set_permissions(default_perms)
            db.session.add(admin)
            db.session.flush()
            
            default_pharmacy = Pharmacy.query.first()
            if default_pharmacy and not UserPharmacy.query.filter_by(user_id=admin.id).first():
                user_pharma = UserPharmacy(
                    user_id=admin.id,
                    pharmacy_id=default_pharmacy.id,
                    is_primary=True,
                    assigned_by=admin.id
                )
                db.session.add(user_pharma)
            
            db.session.commit()
        
        if not Setting.query.filter_by(key='company_name').first():
            default_settings = [
                Setting(key='company_name', value='Pharmacie Moderne', description='Nom de l\'entreprise'),
                Setting(key='company_address', value='', description='Adresse de l\'entreprise'),
                Setting(key='company_phone', value='', description='Téléphone de l\'entreprise'),
                Setting(key='company_email', value='', description='Email de l\'entreprise'),
                Setting(key='currency_symbol', value='$', description='Symbole de la devise'),
                Setting(key='currency_code', value='USD', description='Code de la devise'),
                Setting(key='tax_rate', value='0', description='Taux de taxe par défaut'),
            ]
            for setting in default_settings:
                db.session.add(setting)
            db.session.commit()
        
        from app.models import ExchangeRate
        if not ExchangeRate.query.filter_by(from_currency='USD', to_currency='CDF').first():
            usd_cdf_rate = ExchangeRate(
                from_currency='USD',
                to_currency='CDF',
                rate=2800.0  # Taux par défaut
            )
            db.session.add(usd_cdf_rate)
            db.session.commit()
    
    return app

from flask import Flask
from flask_login import LoginManager
from flask_migrate import Migrate
from app.models import db, User
from app.config import Config

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
    
    with app.app_context():
        db.create_all()
        
        from app.models import User, Setting
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
    
    return app

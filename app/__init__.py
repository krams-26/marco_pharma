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
    
    @app.template_filter('format_json')
    def format_json(value):
        """Formater un dictionnaire en JSON lisible avec accents"""
        import json
        if isinstance(value, dict):
            return json.dumps(value, indent=2, ensure_ascii=False)
        return str(value)
    
    @app.template_filter('usd_to_cdf')
    def usd_to_cdf(amount_usd):
        """Convertir USD en CDF selon le taux de change actuel"""
        from app.models import ExchangeRate, SystemConfig
        if amount_usd is None:
            return 0
        amount_usd = float(amount_usd)
        
        # Récupérer le taux USD -> CDF depuis ExchangeRate
        rate = ExchangeRate.query.filter_by(
            from_currency='USD',
            to_currency='CDF',
            is_active=True
        ).first()
        
        if rate:
            return amount_usd * rate.rate
        
        # Sinon utiliser le taux par défaut dans SystemConfig
        default_rate = SystemConfig.get('default_exchange_rate', 2800)
        return amount_usd * float(default_rate)
    
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
        from app.models import User, SystemConfig
        all_users = []
        if current_user.is_authenticated and current_user.role in ['admin', 'manager']:
            all_users = User.query.filter_by(is_active=True).order_by(User.first_name).all()
        
        # Charger les configurations système pour les templates
        company_config = {}
        if hasattr(current_user, 'is_authenticated'):
            for key in ['company_name', 'company_type', 'company_email', 'company_phone', 
                       'company_website', 'company_address', 'currency_symbol', 
                       'currency_code', 'timezone', 'language']:
                company_config[key] = SystemConfig.get(key, '')
        
        return dict(
            has_any_permission=has_any_permission, 
            all_users=all_users,
            config=company_config
        )
    
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
        
        # Migration: Ajouter la colonne 'result' à la table audits si elle n'existe pas
        from app.models import Audit
        from sqlalchemy import inspect
        try:
            inspector = inspect(db.engine)
            columns = [col['name'] for col in inspector.get_columns('audits')]
            if 'result' not in columns:
                print("Ajout de la colonne 'result' à la table audits...")
                with db.engine.connect() as conn:
                    conn.execute(db.text("ALTER TABLE audits ADD COLUMN result VARCHAR(20) DEFAULT 'success'"))
                    conn.commit()
                print("✓ Colonne 'result' ajoutée avec succès!")
                
                # Mettre à jour les valeurs NULL avec 'success'
                Audit.query.filter(Audit.result == None).update({'result': 'success'})
                db.session.commit()
                print("✓ Valeurs NULL mises à jour avec 'success'.")
        except Exception as e:
            print(f"Note migration audits: {e}")
            try:
                db.session.rollback()
            except:
                pass
        
        from app.models import User, Setting, Pharmacy, UserPharmacy, SystemConfig
        
        # Initialiser les configurations système
        if not SystemConfig.query.first():
            # Informations entreprise
            SystemConfig.set('company_name', 'MARCO PHARMA SARL', 'company', 'string', 'Nom de l\'entreprise')
            SystemConfig.set('company_type', 'SARL', 'company', 'string', 'Type de société')
            SystemConfig.set('company_sector', 'Pharmacie / Distribution pharmaceutique', 'company', 'string', 'Secteur d\'activité')
            SystemConfig.set('company_description', 'Entreprise spécialisée dans la distribution de produits pharmaceutiques', 'company', 'string', 'Description')
            SystemConfig.set('company_founded_year', '2020', 'company', 'string', 'Année de création')
            SystemConfig.set('company_legal_status', 'Société à Responsabilité Limitée', 'company', 'string', 'Statut légal')
            SystemConfig.set('company_email', 'contact@marco-pharma.com', 'company', 'string', 'Email')
            SystemConfig.set('company_phone', '+33 1 23 45 67 89', 'company', 'string', 'Téléphone')
            SystemConfig.set('company_website', 'https://marco-pharma.com', 'company', 'string', 'Site web')
            SystemConfig.set('company_address', '123 Rue de la Pharmacie, 75001 Paris, France', 'company', 'string', 'Adresse')
            
            # Paramètres financiers
            SystemConfig.set('currency_symbol', '$', 'financial', 'string', 'Symbole de devise')
            SystemConfig.set('currency_code', 'USD', 'financial', 'string', 'Code devise')
            SystemConfig.set('secondary_currency', 'CDF', 'financial', 'string', 'Devise secondaire')
            SystemConfig.set('default_exchange_rate', '2800', 'financial', 'number', 'Taux de change par défaut USD-CDF')
            SystemConfig.set('tva_rate', '18.00', 'financial', 'number', 'Taux de TVA')
            SystemConfig.set('min_margin', '20.00', 'financial', 'number', 'Marge minimum')
            
            # Paramètres de stock
            SystemConfig.set('low_stock_threshold', '10', 'stock', 'number', 'Seuil stock bas')
            SystemConfig.set('out_of_stock_threshold', '5', 'stock', 'number', 'Seuil rupture stock')
            SystemConfig.set('expiry_warning_days', '30', 'stock', 'number', 'Jours d\'alerte expiration')
            SystemConfig.set('safety_margin', '15', 'stock', 'number', 'Marge de sécurité')
            
            # Paramètres régionaux
            SystemConfig.set('timezone', 'Europe/Paris', 'regional', 'string', 'Fuseau horaire')
            SystemConfig.set('language', 'fr', 'regional', 'string', 'Langue')
            SystemConfig.set('date_format', 'd/m/Y', 'regional', 'string', 'Format date')
            SystemConfig.set('time_format', 'H:i', 'regional', 'string', 'Format heure')
            
            db.session.commit()
        
        if not Pharmacy.query.first():
            company_name = SystemConfig.get('company_name', 'MARCO PHARMA SARL')
            default_pharmacy = Pharmacy(
                name=f'Pharmacie {company_name} Centrale',
                type='depot',
                code='DEPOT-CENTRAL-001',
                address=SystemConfig.get('company_address', 'Adresse principale'),
                phone=SystemConfig.get('company_phone', '+243 XXX XXX XXX'),
                email=SystemConfig.get('company_email', 'central@marcophar.com'),
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

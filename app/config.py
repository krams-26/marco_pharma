import os
from datetime import timedelta

basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    # En production, définir SECRET_KEY dans les variables d'environnement
    # Générer une clé sécurisée avec: python -c "import secrets; print(secrets.token_hex(32))"
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production-CHANGE-IN-PRODUCTION'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'mysql+pymysql://root:@localhost:3306/marphar'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    PERMANENT_SESSION_LIFETIME = timedelta(hours=12)
    
    UPLOAD_FOLDER = 'uploads'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024
    
    ITEMS_PER_PAGE = 20
    
    # 1. INFORMATIONS DE BASE
    COMPANY_NAME = 'MARCO PHARMA SARL'
    COMPANY_TYPE = 'SARL'
    COMPANY_SECTOR = 'Pharmacie / Distribution pharmaceutique'
    COMPANY_DESCRIPTION = 'Entreprise spécialisée dans la distribution de produits pharmaceutiques'
    COMPANY_FOUNDED_YEAR = '2020'
    COMPANY_LEGAL_STATUS = 'Société à Responsabilité Limitée'
    
    # 2. COORDONNÉES DE CONTACT
    COMPANY_EMAIL = 'contact@marco-pharma.com'
    COMPANY_PHONE = '+33 1 23 45 67 89'
    COMPANY_WEBSITE = 'https://marco-pharma.com'
    COMPANY_ADDRESS = '123 Rue de la Pharmacie, 75001 Paris, France'
    COMPANY_STREET = '123 Rue de la Pharmacie'
    COMPANY_POSTAL_CODE = '75001'
    COMPANY_CITY = 'Paris'
    COMPANY_COUNTRY = 'France'
    
    # 3. INFORMATIONS LÉGALES
    COMPANY_RCCM = ''
    COMPANY_NATIONAL_ID = ''
    COMPANY_TAX_NUMBER = ''
    COMPANY_VAT_NUMBER = ''
    COMPANY_REGISTRATION_DATE = ''
    COMPANY_LEGAL_REPRESENTATIVE = ''
    
    # Paramètres financiers
    CURRENCY_SYMBOL = '$'
    CURRENCY_CODE = 'USD'
    SECONDARY_CURRENCY = 'CDF'
    EXCHANGE_RATE = 3100
    TVA_RATE = 18.00
    MIN_MARGIN = 20.00
    
    # Paramètres de stock
    LOW_STOCK_THRESHOLD = 10
    OUT_OF_STOCK_THRESHOLD = 5
    EXPIRY_WARNING_DAYS = 30
    SAFETY_MARGIN = 15
    
    # Paramètres régionaux
    TIMEZONE = 'Europe/Paris'
    LANGUAGE = 'fr'
    DATE_FORMAT = 'd/m/Y'
    TIME_FORMAT = 'H:i'

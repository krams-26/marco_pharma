import os
from datetime import timedelta

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///pharmacy.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    PERMANENT_SESSION_LIFETIME = timedelta(hours=12)
    
    UPLOAD_FOLDER = 'uploads'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024
    
    ITEMS_PER_PAGE = 20
    
    CURRENCY_SYMBOL = '$'
    CURRENCY_CODE = 'USD'
    
    COMPANY_NAME = 'Pharmacie Moderne'
    COMPANY_ADDRESS = ''
    COMPANY_PHONE = ''
    COMPANY_EMAIL = ''

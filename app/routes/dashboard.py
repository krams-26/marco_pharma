from flask import Blueprint, render_template
from flask_login import login_required, current_user
from app.models import db, Product, Sale, Customer, User, StockMovement
from app.decorators import require_permission
from sqlalchemy import func
from datetime import datetime, timedelta

dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/dashboard')

def get_user_scope():
    """Déterminer le scope d'accès de l'utilisateur"""
    if current_user.role == 'admin':
        return 'all'
    elif current_user.role in ['manager', 'pharmacien']:
        return 'pharmacy'
    else:
        return 'personal'

def filter_by_scope(query, model):
    """Filtrer une requête selon le scope de l'utilisateur"""
    scope = get_user_scope()
    
    if scope == 'all':
        return query
    
    primary_pharmacy = current_user.get_primary_pharmacy()
    
    if scope == 'pharmacy' and primary_pharmacy:
        if hasattr(model, 'pharmacy_id'):
            return query.filter(model.pharmacy_id == primary_pharmacy.id)
    
    if scope == 'personal':
        if hasattr(model, 'user_id'):
            return query.filter(model.user_id == current_user.id)
        elif hasattr(model, 'pharmacy_id') and primary_pharmacy:
            return query.filter(model.pharmacy_id == primary_pharmacy.id)
    
    return query

@dashboard_bp.route('/')
@require_permission('view_dashboard')
def index():
    today = datetime.now().date()
    month_start = datetime(today.year, today.month, 1).date()
    scope = get_user_scope()
    primary_pharmacy = current_user.get_primary_pharmacy()
    
    # Requêtes filtrées selon le scope
    products_query = Product.query.filter_by(is_active=True)
    products_query = filter_by_scope(products_query, Product)
    total_products = products_query.count()
    
    low_stock_query = Product.query.filter(
        Product.is_active == True,
        Product.stock_quantity <= Product.min_stock_level
    )
    low_stock_query = filter_by_scope(low_stock_query, Product)
    low_stock_products = low_stock_query.count()
    
    expired_query = Product.query.filter(
        Product.is_active == True,
        Product.expiry_date < today
    )
    expired_query = filter_by_scope(expired_query, Product)
    expired_products = expired_query.count()
    
    customers_query = Customer.query.filter_by(is_active=True)
    total_customers = customers_query.count()
    
    # Ventes du jour
    today_sales_query = Sale.query.filter(func.date(Sale.sale_date) == today)
    today_sales_query = filter_by_scope(today_sales_query, Sale)
    today_sales = today_sales_query.all()
    today_revenue = sum(sale.total_amount for sale in today_sales)
    
    # Ventes du mois
    month_sales_query = Sale.query.filter(func.date(Sale.sale_date) >= month_start)
    month_sales_query = filter_by_scope(month_sales_query, Sale)
    month_sales = month_sales_query.all()
    month_revenue = sum(sale.total_amount for sale in month_sales)
    
    # Paiements en attente
    pending_query = Sale.query.filter(Sale.payment_status.in_(['pending', 'partial']))
    pending_query = filter_by_scope(pending_query, Sale)
    pending_payments = pending_query.count()
    
    # Ventes récentes
    recent_sales_query = Sale.query
    recent_sales_query = filter_by_scope(recent_sales_query, Sale)
    recent_sales = recent_sales_query.order_by(Sale.sale_date.desc()).limit(10).all()
    
    # Articles en rupture
    low_stock_items_query = Product.query.filter(
        Product.is_active == True,
        Product.stock_quantity <= Product.min_stock_level
    )
    low_stock_items_query = filter_by_scope(low_stock_items_query, Product)
    low_stock_items = low_stock_items_query.order_by(Product.stock_quantity).limit(10).all()
    
    return render_template('dashboard/index.html',
                         total_products=total_products,
                         low_stock_products=low_stock_products,
                         expired_products=expired_products,
                         total_customers=total_customers,
                         today_revenue=today_revenue,
                         month_revenue=month_revenue,
                         pending_payments=pending_payments,
                         recent_sales=recent_sales,
                         low_stock_items=low_stock_items,
                         scope=scope,
                         pharmacy_name=primary_pharmacy.name if primary_pharmacy else 'Toutes')

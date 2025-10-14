from flask import Blueprint, render_template
from flask_login import login_required, current_user
from app.models import db, Product, Sale, Customer, User, StockMovement
from app.decorators import require_permission
from sqlalchemy import func
from datetime import datetime, timedelta

dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/dashboard')

@dashboard_bp.route('/')
@require_permission('view_dashboard')
def index():
    today = datetime.now().date()
    month_start = datetime(today.year, today.month, 1).date()
    
    total_products = Product.query.filter_by(is_active=True).count()
    low_stock_products = Product.query.filter(
        Product.is_active == True,
        Product.stock_quantity <= Product.min_stock_level
    ).count()
    
    expired_products = Product.query.filter(
        Product.is_active == True,
        Product.expiry_date < today
    ).count()
    
    total_customers = Customer.query.filter_by(is_active=True).count()
    
    today_sales = Sale.query.filter(
        func.date(Sale.sale_date) == today
    ).all()
    today_revenue = sum(sale.total_amount for sale in today_sales)
    
    month_sales = Sale.query.filter(
        func.date(Sale.sale_date) >= month_start
    ).all()
    month_revenue = sum(sale.total_amount for sale in month_sales)
    
    pending_payments = Sale.query.filter(
        Sale.payment_status.in_(['pending', 'partial'])
    ).count()
    
    recent_sales = Sale.query.order_by(Sale.sale_date.desc()).limit(10).all()
    
    low_stock_items = Product.query.filter(
        Product.is_active == True,
        Product.stock_quantity <= Product.min_stock_level
    ).order_by(Product.stock_quantity).limit(10).all()
    
    return render_template('dashboard/index.html',
                         total_products=total_products,
                         low_stock_products=low_stock_products,
                         expired_products=expired_products,
                         total_customers=total_customers,
                         today_revenue=today_revenue,
                         month_revenue=month_revenue,
                         pending_payments=pending_payments,
                         recent_sales=recent_sales,
                         low_stock_items=low_stock_items)

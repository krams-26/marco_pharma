from flask import Blueprint, render_template, request, send_file
from flask_login import login_required
from app.models import db, Sale, Product, Expense, Payment, Customer
from app.decorators import require_permission
from sqlalchemy import func, extract
from datetime import datetime, timedelta
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from openpyxl import Workbook
import io

reports_bp = Blueprint('reports', __name__, url_prefix='/reports')

@reports_bp.route('/')
@require_permission('view_reports')
def index():
    return render_template('reports/index.html')

@reports_bp.route('/sales')
@login_required
def sales():
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    
    if not date_from:
        date_from = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
    if not date_to:
        date_to = datetime.now().strftime('%Y-%m-%d')
    
    sales_data = Sale.query.filter(
        Sale.sale_date >= datetime.strptime(date_from, '%Y-%m-%d'),
        Sale.sale_date <= datetime.strptime(date_to, '%Y-%m-%d')
    ).all()
    
    total_sales = sum(sale.total_amount for sale in sales_data)
    total_paid = sum(sale.paid_amount for sale in sales_data)
    total_due = total_sales - total_paid
    
    return render_template('reports/sales.html',
                         sales=sales_data,
                         total_sales=total_sales,
                         total_paid=total_paid,
                         total_due=total_due,
                         date_from=date_from,
                         date_to=date_to)

@reports_bp.route('/expenses')
@login_required
def expenses():
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    
    if not date_from:
        date_from = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
    if not date_to:
        date_to = datetime.now().strftime('%Y-%m-%d')
    
    expenses_data = Expense.query.filter(
        Expense.expense_date >= datetime.strptime(date_from, '%Y-%m-%d').date(),
        Expense.expense_date <= datetime.strptime(date_to, '%Y-%m-%d').date()
    ).all()
    
    total_expenses = sum(exp.amount for exp in expenses_data)
    
    return render_template('reports/expenses.html',
                         expenses=expenses_data,
                         total_expenses=total_expenses,
                         date_from=date_from,
                         date_to=date_to)

@reports_bp.route('/monthly')
@login_required
def monthly():
    year = request.args.get('year', datetime.now().year, type=int)
    month = request.args.get('month', datetime.now().month, type=int)
    
    start_date = datetime(year, month, 1)
    if month == 12:
        end_date = datetime(year + 1, 1, 1)
    else:
        end_date = datetime(year, month + 1, 1)
    
    sales_data = Sale.query.filter(
        Sale.sale_date >= start_date,
        Sale.sale_date < end_date
    ).all()
    
    total_revenue = sum(sale.total_amount for sale in sales_data)
    
    expenses_data = Expense.query.filter(
        Expense.expense_date >= start_date.date(),
        Expense.expense_date < end_date.date()
    ).all()
    
    total_expenses = sum(exp.amount for exp in expenses_data)
    
    profit = total_revenue - total_expenses
    
    return render_template('reports/monthly.html',
                         sales=sales_data,
                         expenses=expenses_data,
                         total_revenue=total_revenue,
                         total_expenses=total_expenses,
                         profit=profit,
                         year=year,
                         month=month)

@reports_bp.route('/stock')
@login_required
def stock():
    products = Product.query.filter_by(is_active=True).order_by(Product.stock_quantity).all()
    
    low_stock = [p for p in products if p.is_low_stock]
    total_value = sum(p.stock_quantity * p.purchase_price for p in products)
    
    return render_template('reports/stock.html',
                         products=products,
                         low_stock=low_stock,
                         total_value=total_value)

@reports_bp.route('/customers')
@login_required
def customers():
    customers_data = Customer.query.filter_by(is_active=True).all()
    
    customer_stats = []
    for customer in customers_data:
        total_purchases = sum(sale.total_amount for sale in customer.sales)
        total_paid = sum(sale.paid_amount for sale in customer.sales)
        balance = total_purchases - total_paid
        
        customer_stats.append({
            'customer': customer,
            'total_purchases': total_purchases,
            'total_paid': total_paid,
            'balance': balance
        })
    
    customer_stats.sort(key=lambda x: x['total_purchases'], reverse=True)
    
    return render_template('reports/customers.html', customer_stats=customer_stats)

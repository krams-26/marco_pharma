from flask import Blueprint, render_template, request, send_file
from flask_login import login_required, current_user
from app.models import db, Sale, Product, Expense, Payment, Customer
from app.decorators import require_permission
from app.pharmacy_utils import filter_by_pharmacy, get_accessible_pharmacies
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
    pharmacy_filter = request.args.get('pharmacy_id', 'all')
    
    if not date_from:
        date_from = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
    if not date_to:
        date_to = datetime.now().strftime('%Y-%m-%d')
    
    query = Sale.query.filter(
        Sale.sale_date >= datetime.strptime(date_from, '%Y-%m-%d'),
        Sale.sale_date <= datetime.strptime(date_to, '%Y-%m-%d')
    )
    
    query = filter_by_pharmacy(query, Sale, pharmacy_filter)
    sales_data = query.all()
    
    total_sales = sum(sale.total_amount for sale in sales_data)
    total_paid = sum(sale.paid_amount for sale in sales_data)
    total_due = total_sales - total_paid
    
    pharmacies = get_accessible_pharmacies()
    
    return render_template('reports/sales.html',
                         sales=sales_data,
                         total_sales=total_sales,
                         total_paid=total_paid,
                         total_due=total_due,
                         date_from=date_from,
                         date_to=date_to,
                         pharmacies=pharmacies,
                         pharmacy_filter=pharmacy_filter)

@reports_bp.route('/expenses')
@login_required
def expenses():
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    pharmacy_filter = request.args.get('pharmacy_id', 'all')
    
    if not date_from:
        date_from = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
    if not date_to:
        date_to = datetime.now().strftime('%Y-%m-%d')
    
    query = Expense.query.filter(
        Expense.expense_date >= datetime.strptime(date_from, '%Y-%m-%d').date(),
        Expense.expense_date <= datetime.strptime(date_to, '%Y-%m-%d').date()
    )
    
    query = filter_by_pharmacy(query, Expense, pharmacy_filter)
    expenses_data = query.all()
    
    total_expenses = sum(exp.amount for exp in expenses_data)
    
    pharmacies = get_accessible_pharmacies()
    
    return render_template('reports/expenses.html',
                         expenses=expenses_data,
                         total_expenses=total_expenses,
                         date_from=date_from,
                         date_to=date_to,
                         pharmacies=pharmacies,
                         pharmacy_filter=pharmacy_filter)

@reports_bp.route('/monthly')
@login_required
def monthly():
    year = request.args.get('year', datetime.now().year, type=int)
    month = request.args.get('month', datetime.now().month, type=int)
    pharmacy_filter = request.args.get('pharmacy_id', 'all')
    
    start_date = datetime(year, month, 1)
    if month == 12:
        end_date = datetime(year + 1, 1, 1)
    else:
        end_date = datetime(year, month + 1, 1)
    
    sales_query = Sale.query.filter(
        Sale.sale_date >= start_date,
        Sale.sale_date < end_date
    )
    sales_query = filter_by_pharmacy(sales_query, Sale, pharmacy_filter)
    sales_data = sales_query.all()
    
    total_revenue = sum(sale.total_amount for sale in sales_data)
    
    expenses_query = Expense.query.filter(
        Expense.expense_date >= start_date.date(),
        Expense.expense_date < end_date.date()
    )
    expenses_query = filter_by_pharmacy(expenses_query, Expense, pharmacy_filter)
    expenses_data = expenses_query.all()
    
    total_expenses = sum(exp.amount for exp in expenses_data)
    
    profit = total_revenue - total_expenses
    
    pharmacies = get_accessible_pharmacies()
    
    return render_template('reports/monthly.html',
                         sales=sales_data,
                         expenses=expenses_data,
                         total_revenue=total_revenue,
                         total_expenses=total_expenses,
                         profit=profit,
                         year=year,
                         month=month,
                         pharmacies=pharmacies,
                         pharmacy_filter=pharmacy_filter)

@reports_bp.route('/stock')
@login_required
def stock():
    pharmacy_filter = request.args.get('pharmacy_id', 'all')
    
    query = Product.query.filter_by(is_active=True)
    query = filter_by_pharmacy(query, Product, pharmacy_filter)
    products = query.order_by(Product.stock_quantity).all()
    
    low_stock = [p for p in products if p.is_low_stock]
    total_value = sum(p.stock_quantity * p.purchase_price for p in products)
    
    pharmacies = get_accessible_pharmacies()
    
    return render_template('reports/stock.html',
                         products=products,
                         low_stock=low_stock,
                         total_value=total_value,
                         pharmacies=pharmacies,
                         pharmacy_filter=pharmacy_filter)

@reports_bp.route('/customers')
@login_required
def customers():
    pharmacy_filter = request.args.get('pharmacy_id', 'all')
    
    customers_data = Customer.query.filter_by(is_active=True).all()
    
    customer_stats = []
    for customer in customers_data:
        sales_query = Sale.query.filter_by(customer_id=customer.id)
        sales_query = filter_by_pharmacy(sales_query, Sale, pharmacy_filter)
        sales = sales_query.all()
        
        if not sales:
            continue
        
        total_purchases = sum(sale.total_amount for sale in sales)
        total_paid = sum(sale.paid_amount for sale in sales)
        balance = total_purchases - total_paid
        
        customer_stats.append({
            'customer': customer,
            'total_purchases': total_purchases,
            'total_paid': total_paid,
            'balance': balance
        })
    
    customer_stats.sort(key=lambda x: x['total_purchases'], reverse=True)
    
    pharmacies = get_accessible_pharmacies()
    
    return render_template('reports/customers.html', 
                         customer_stats=customer_stats,
                         pharmacies=pharmacies,
                         pharmacy_filter=pharmacy_filter)

@reports_bp.route('/pharmacies')
@require_permission('view_reports')
def pharmacies():
    from app.models import Pharmacy
    
    pharmacies_list = Pharmacy.query.filter_by(is_active=True).all()
    
    pharmacy_stats = []
    for pharmacy in pharmacies_list:
        total_sales = db.session.query(func.sum(Sale.total_amount)).filter_by(pharmacy_id=pharmacy.id).scalar() or 0
        sales_count = Sale.query.filter_by(pharmacy_id=pharmacy.id).count()
        total_paid = db.session.query(func.sum(Sale.paid_amount)).filter_by(pharmacy_id=pharmacy.id).scalar() or 0
        total_pending = total_sales - total_paid
        
        products_count = Product.query.filter_by(pharmacy_id=pharmacy.id, is_active=True).count()
        low_stock_count = Product.query.filter(
            Product.pharmacy_id == pharmacy.id,
            Product.is_active == True,
            Product.stock_quantity <= Product.min_stock_level
        ).count()
        
        stock_value = db.session.query(
            func.sum(Product.stock_quantity * Product.purchase_price)
        ).filter_by(pharmacy_id=pharmacy.id, is_active=True).scalar() or 0
        
        progress = (total_sales / pharmacy.revenue_target * 100) if pharmacy.revenue_target > 0 else 0
        
        pharmacy_stats.append({
            'pharmacy': pharmacy,
            'total_sales': total_sales,
            'sales_count': sales_count,
            'total_paid': total_paid,
            'total_pending': total_pending,
            'products_count': products_count,
            'low_stock_count': low_stock_count,
            'stock_value': stock_value,
            'target_progress': progress
        })
    
    pharmacy_stats.sort(key=lambda x: x['total_sales'], reverse=True)
    
    grand_total = sum(p['total_sales'] for p in pharmacy_stats)
    
    return render_template('reports/pharmacies.html', 
                         pharmacy_stats=pharmacy_stats,
                         grand_total=grand_total)

@reports_bp.route('/products')
@require_permission('view_reports')
def products():
    from app.models import SaleItem
    
    products_sales = db.session.query(
        Product.id,
        Product.name,
        Product.category,
        Product.stock_quantity,
        Product.selling_price,
        Product.purchase_price,
        func.count(SaleItem.id).label('sales_count'),
        func.sum(SaleItem.quantity).label('total_sold'),
        func.sum(SaleItem.total).label('total_revenue')
    ).join(SaleItem, Product.id == SaleItem.product_id, isouter=True)\
     .filter(Product.is_active == True)\
     .group_by(Product.id)\
     .order_by(func.sum(SaleItem.total).desc())\
     .all()
    
    product_stats = []
    for p in products_sales:
        margin = p.selling_price - p.purchase_price
        margin_percent = (margin / p.purchase_price * 100) if p.purchase_price > 0 else 0
        total_sold = p.total_sold or 0
        total_revenue = p.total_revenue or 0
        
        product_stats.append({
            'name': p.name,
            'category': p.category,
            'stock': p.stock_quantity,
            'sales_count': p.sales_count or 0,
            'total_sold': total_sold,
            'total_revenue': total_revenue,
            'selling_price': p.selling_price,
            'margin': margin,
            'margin_percent': margin_percent
        })
    
    total_products = len(product_stats)
    total_revenue = sum(p['total_revenue'] for p in product_stats)
    avg_margin = sum(p['margin_percent'] for p in product_stats) / total_products if total_products > 0 else 0
    
    return render_template('reports/products.html',
                         product_stats=product_stats,
                         total_products=total_products,
                         total_revenue=total_revenue,
                         avg_margin=avg_margin)

@reports_bp.route('/export/pharmacies-excel')
@require_permission('view_reports')
def export_pharmacies_excel():
    from app.models import Pharmacy
    
    pharmacies_list = Pharmacy.query.filter_by(is_active=True).all()
    
    wb = Workbook()
    ws = wb.active
    ws.title = "Pharmacies"
    
    ws.append(['Pharmacie', 'Type', 'Ventes', 'CA Total ($)', 'Produits', 'Valeur Stock ($)', 'Objectif ($)', 'Progression %'])
    
    for pharmacy in pharmacies_list:
        total_sales = db.session.query(func.sum(Sale.total_amount)).filter_by(pharmacy_id=pharmacy.id).scalar() or 0
        sales_count = Sale.query.filter_by(pharmacy_id=pharmacy.id).count()
        products_count = Product.query.filter_by(pharmacy_id=pharmacy.id, is_active=True).count()
        stock_value = db.session.query(func.sum(Product.stock_quantity * Product.purchase_price)).filter_by(pharmacy_id=pharmacy.id, is_active=True).scalar() or 0
        progress = (total_sales / pharmacy.revenue_target * 100) if pharmacy.revenue_target > 0 else 0
        
        ws.append([
            pharmacy.name,
            pharmacy.type,
            sales_count,
            total_sales,
            products_count,
            stock_value,
            pharmacy.revenue_target,
            f'{progress:.1f}%'
        ])
    
    output = io.BytesIO()
    wb.save(output)
    output.seek(0)
    
    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name=f'rapport_pharmacies_{datetime.now().strftime("%Y%m%d")}.xlsx'
    )

@reports_bp.route('/export/products-excel')
@require_permission('view_reports')
def export_products_excel():
    from app.models import SaleItem
    
    products_sales = db.session.query(
        Product.name,
        Product.category,
        Product.stock_quantity,
        Product.selling_price,
        Product.purchase_price,
        func.sum(SaleItem.quantity).label('total_sold'),
        func.sum(SaleItem.total).label('total_revenue')
    ).join(SaleItem, Product.id == SaleItem.product_id, isouter=True)\
     .filter(Product.is_active == True)\
     .group_by(Product.id)\
     .order_by(func.sum(SaleItem.total).desc())\
     .all()
    
    wb = Workbook()
    ws = wb.active
    ws.title = "Produits"
    
    ws.append(['Produit', 'Catégorie', 'Stock', 'Prix Vente ($)', 'Prix Achat ($)', 'Qté Vendue', 'CA Total ($)', 'Marge %'])
    
    for p in products_sales:
        total_sold = p.total_sold or 0
        total_revenue = p.total_revenue or 0
        margin = p.selling_price - p.purchase_price
        margin_percent = (margin / p.purchase_price * 100) if p.purchase_price > 0 else 0
        
        ws.append([
            p.name,
            p.category or '-',
            p.stock_quantity,
            p.selling_price,
            p.purchase_price,
            total_sold,
            total_revenue,
            f'{margin_percent:.1f}%'
        ])
    
    output = io.BytesIO()
    wb.save(output)
    output.seek(0)
    
    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name=f'rapport_produits_{datetime.now().strftime("%Y%m%d")}.xlsx'
    )

@reports_bp.route('/export/sales-excel')
@require_permission('view_reports')
def export_sales_excel():
    from app.export_utils import export_to_excel
    
    # Récupérer les ventes
    sales = Sale.query.order_by(Sale.sale_date.desc()).all()
    
    # Préparer les données
    data = []
    for sale in sales:
        data.append({
            'Numéro': sale.invoice_number,
            'Date': sale.sale_date.strftime('%d/%m/%Y %H:%M') if sale.sale_date else '',
            'Client': sale.customer.name if sale.customer else 'Anonyme',
            'Total': sale.total_amount,
            'Payé': sale.paid_amount,
            'Solde': sale.balance_due,
            'Statut': sale.payment_status,
            'Pharmacie': sale.pharmacy.name if sale.pharmacy else 'N/A'
        })
    
    headers = ['Numéro', 'Date', 'Client', 'Total', 'Payé', 'Solde', 'Statut', 'Pharmacie']
    
    return export_to_excel(
        data, 
        'rapport_ventes', 
        headers, 
        'Ventes',
        download_name=f'rapport_ventes_{datetime.now().strftime("%Y%m%d")}.xlsx'
    )

@reports_bp.route('/export/customers-excel')
@require_permission('view_reports')
def export_customers_excel():
    from app.export_utils import export_to_excel
    
    # Récupérer les clients
    customers = Customer.query.order_by(Customer.name).all()
    
    # Préparer les données
    data = []
    for customer in customers:
        # Calculer le total des achats
        total_purchases = db.session.query(func.sum(Sale.total_amount)).filter_by(customer_id=customer.id).scalar() or 0
        
        data.append({
            'Nom': customer.name,
            'Type': customer.customer_type,
            'Email': customer.email or '',
            'Téléphone': customer.phone or '',
            'Adresse': customer.address or '',
            'Total Achats': total_purchases,
            'Statut': 'Actif' if customer.is_active else 'Inactif'
        })
    
    headers = ['Nom', 'Type', 'Email', 'Téléphone', 'Adresse', 'Total Achats', 'Statut']
    
    return export_to_excel(
        data, 
        'rapport_clients', 
        headers, 
        'Clients',
        download_name=f'rapport_clients_{datetime.now().strftime("%Y%m%d")}.xlsx'
    )

@reports_bp.route('/export/stock-excel')
@require_permission('view_reports')
def export_stock_excel():
    from app.export_utils import export_to_excel
    
    # Récupérer les produits
    products = Product.query.filter_by(is_active=True).order_by(Product.name).all()
    
    # Préparer les données
    data = []
    for product in products:
        data.append({
            'Nom': product.name,
            'Code-barres': product.barcode or '',
            'Catégorie': product.category or '',
            'Stock': product.stock_quantity,
            'Stock Min': product.min_stock_level,
            'Prix Achat': product.purchase_price,
            'Prix Vente': product.selling_price,
            'Prix Gros': product.wholesale_price,
            'Statut Stock': 'Faible' if product.stock_quantity <= product.min_stock_level else 'Normal'
        })
    
    headers = ['Nom', 'Code-barres', 'Catégorie', 'Stock', 'Stock Min', 'Prix Achat', 'Prix Vente', 'Prix Gros', 'Statut Stock']
    
    return export_to_excel(
        data, 
        'rapport_stock', 
        headers, 
        'Stock',
        download_name=f'rapport_stock_{datetime.now().strftime("%Y%m%d")}.xlsx'
    )

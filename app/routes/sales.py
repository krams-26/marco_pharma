from flask import Blueprint, render_template, request
from flask_login import login_required
from app.models import Sale

sales_bp = Blueprint('sales', __name__, url_prefix='/sales')

@sales_bp.route('/')
@login_required
def index():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    
    query = Sale.query
    
    if search:
        query = query.filter(Sale.invoice_number.ilike(f'%{search}%'))
    
    sales = query.order_by(Sale.sale_date.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    
    return render_template('sales/index.html', sales=sales, search=search)

@sales_bp.route('/view/<int:id>')
@login_required
def view(id):
    sale = Sale.query.get_or_404(id)
    return render_template('sales/view.html', sale=sale)

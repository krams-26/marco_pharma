from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app import db
from app.models import Sale, SaleItem, Product, Audit, TempSale, StockMovement, Payment, Proforma, ProformaItem, Customer
from app.decorators import require_permission
from app.pharmacy_utils import filter_by_pharmacy, get_accessible_pharmacies, is_admin
from app.export_utils import export_to_csv, export_to_excel
from datetime import datetime, timedelta
import json
import random

sales_bp = Blueprint('sales', __name__, url_prefix='/sales')

@sales_bp.route('/')
@require_permission('manage_sales')
def index():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    pharmacy_filter = request.args.get('pharmacy_id', 'all')
    status_filter = request.args.get('status', '')
    view_type = request.args.get('view', 'all')
    
    # Récupérer les ventes finales
    final_sales_query = Sale.query
    final_sales_query = filter_by_pharmacy(final_sales_query, Sale, pharmacy_filter)
    
    if search:
        final_sales_query = final_sales_query.filter(Sale.invoice_number.ilike(f'%{search}%'))
    
    if status_filter:
        final_sales_query = final_sales_query.filter(Sale.payment_status == status_filter)
    
    # Récupérer les ventes temporaires
    temp_sales_query = TempSale.query
    temp_sales_query = filter_by_pharmacy(temp_sales_query, TempSale, pharmacy_filter)
    
    if search:
        temp_sales_query = temp_sales_query.filter(TempSale.reference.ilike(f'%{search}%'))
    
    # Combiner les résultats
    final_sales = final_sales_query.order_by(Sale.sale_date.desc()).all()
    temp_sales = temp_sales_query.order_by(TempSale.created_at.desc()).all()
    
    # Créer une liste unifiée avec métadonnées
    all_sales = []
    
    if view_type in ['all', 'temp']:
        for ts in temp_sales:
            all_sales.append({
                'type': 'temp',
                'id': ts.id,
                'reference': ts.reference,
                'date': ts.created_at,
                'customer': ts.customer.name if ts.customer else 'Anonyme',
                'total': ts.total_amount,
                'paid': 0,
                'status': ts.status,
                'seller': ts.creator.full_name,
                'data': ts
            })
    
    if view_type in ['all', 'final']:
        for s in final_sales:
            all_sales.append({
                'type': 'final',
                'id': s.id,
                'reference': s.invoice_number,
                'date': s.sale_date,
                'customer': s.customer.name if s.customer else 'Anonyme',
                'total': s.total_amount,
                'paid': s.paid_amount,
                'status': s.payment_status,
                'seller': s.seller.full_name if s.seller else 'N/A',
                'data': s
            })
    
    # Trier par date décroissante
    all_sales.sort(key=lambda x: x['date'], reverse=True)
    
    # Paginer manuellement
    per_page = 10
    total = len(all_sales)
    start = (page - 1) * per_page
    end = start + per_page
    paginated_sales = all_sales[start:end]
    
    pharmacies = get_accessible_pharmacies() if is_admin() else []
    
    stats = {
        'pending_validation': TempSale.query.filter_by(status='pending').count()
    }
    
    return render_template('sales/index.html', 
                         sales=paginated_sales,
                         page=page,
                         total_pages=(total // per_page) + (1 if total % per_page > 0 else 0),
                         has_prev=page > 1,
                         has_next=end < total,
                         search=search,
                         pharmacies=pharmacies,
                         pharmacy_filter=pharmacy_filter,
                         status_filter=status_filter,
                         view_type=view_type,
                         stats=stats)

@sales_bp.route('/export/<format>')
@require_permission('manage_sales')
def export(format):
    pharmacy_filter = request.args.get('pharmacy_id', 'all')
    search = request.args.get('search', '')
    
    query = Sale.query
    query = filter_by_pharmacy(query, Sale, pharmacy_filter)
    
    if search:
        query = query.filter(Sale.invoice_number.ilike(f'%{search}%'))
    
    sales = query.order_by(Sale.sale_date.desc()).all()
    
    headers = ['Facture', 'Date', 'Client', 'Montant Total', 'Payé', 'Solde Dû', 'Statut', 'Pharmacie']
    
    data = []
    for s in sales:
        data.append({
            'Facture': s.invoice_number,
            'Date': s.sale_date.strftime('%d/%m/%Y %H:%M'),
            'Client': s.customer.name if s.customer else 'Anonyme',
            'Montant Total': s.total_amount,
            'Payé': s.paid_amount,
            'Solde Dû': s.balance_due,
            'Statut': s.payment_status,
            'Pharmacie': s.pharmacy.name if s.pharmacy else 'N/A'
        })
    
    if format == 'csv':
        return export_to_csv(data, 'ventes', headers)
    else:
        return export_to_excel(data, 'ventes', headers, 'Ventes')

@sales_bp.route('/view/<int:id>')
@require_permission('manage_sales')
def view(id):
    sale = Sale.query.get_or_404(id)
    return render_template('sales/view.html', sale=sale)

@sales_bp.route('/quick-view/<int:id>')
@require_permission('manage_sales')
def quick_view(id):
    sale = Sale.query.get_or_404(id)
    return jsonify({
        'invoice_number': sale.invoice_number,
        'customer': sale.customer.name if sale.customer else 'Anonyme',
        'seller': sale.seller.full_name if sale.seller else 'N/A',
        'date': sale.sale_date.strftime('%d/%m/%Y %H:%M'),
        'total_amount': sale.total_amount,
        'paid_amount': sale.paid_amount,
        'balance_due': sale.balance_due,
        'discount': sale.discount,
        'payment_status': sale.payment_status,
        'payment_method': sale.payment_method,
        'notes': sale.notes,
        'items': [{
            'name': item.product.name if item.product else 'Produit supprimé',
            'quantity': item.quantity,
            'unit_price': item.unit_price,
            'total': item.total
        } for item in sale.items]
    })

@sales_bp.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
@require_permission('edit_sales')
def edit(id):
    sale = Sale.query.get_or_404(id)
    
    if sale.payment_status == 'paid':
        flash('Impossible de modifier une vente entièrement payée', 'danger')
        return redirect(url_for('sales.view', id=id))
    
    if request.method == 'POST':
        try:
            edit_reason = request.form.get('edit_reason')
            if not edit_reason:
                flash('La raison de la modification est obligatoire', 'danger')
                return redirect(url_for('sales.edit', id=id))
            
            old_total = sale.total_amount
            old_items = {item.product_id: item.quantity for item in sale.items}
            
            sale.discount = float(request.form.get('discount', 0))
            sale.tax = float(request.form.get('tax', 0))
            sale.notes = request.form.get('notes', '')
            
            product_ids = request.form.getlist('product_id[]')
            quantities = request.form.getlist('quantity[]')
            prices = request.form.getlist('price[]')
            
            for item in sale.items:
                product = Product.query.get(item.product_id)
                if product:
                    product.stock_quantity += item.quantity
            
            db.session.query(SaleItem).filter_by(sale_id=sale.id).delete()
            
            new_total = 0
            for pid, qty, price in zip(product_ids, quantities, prices):
                if pid and qty and price:
                    product = Product.query.get(int(pid))
                    if not product:
                        continue
                    
                    quantity = int(qty)
                    unit_price = float(price)
                    
                    if product.stock_quantity < quantity:
                        flash(f'Stock insuffisant pour {product.name}', 'danger')
                        db.session.rollback()
                        return redirect(url_for('sales.edit', id=id))
                    
                    product.stock_quantity -= quantity
                    
                    item_total = quantity * unit_price
                    new_total += item_total
                    
                    sale_item = SaleItem(
                        sale_id=sale.id,
                        product_id=product.id,
                        quantity=quantity,
                        unit_price=unit_price,
                        total=item_total
                    )
                    db.session.add(sale_item)
            
            sale.total_amount = new_total - sale.discount + sale.tax
            sale.remaining_amount = sale.total_amount - sale.paid_amount
            
            if sale.remaining_amount <= 0:
                sale.payment_status = 'paid'
            elif sale.paid_amount > 0:
                sale.payment_status = 'partial'
            else:
                sale.payment_status = 'pending'
            
            sale.is_edited = True
            sale.edited_by = current_user.id
            sale.edited_at = datetime.utcnow()
            sale.edit_reason = edit_reason
            
            audit = Audit(
                user_id=current_user.id,
                action='edit_sale',
                description=f'Modification de la vente {sale.invoice_number}. Raison: {edit_reason}. Ancien total: ${old_total:.2f}, Nouveau total: ${sale.total_amount:.2f}',
                ip_address=request.remote_addr
            )
            db.session.add(audit)
            
            db.session.commit()
            
            flash('Vente modifiée avec succès', 'success')
            return redirect(url_for('sales.view', id=sale.id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Erreur: {str(e)}', 'danger')
            return redirect(url_for('sales.edit', id=id))
    
    products = Product.query.filter_by(is_active=True).all()
    return render_template('sales/edit.html', sale=sale, products=products)

@sales_bp.route('/delete/<int:id>', methods=['POST'])
@login_required
@require_permission('delete_sales')
def delete(id):
    sale = Sale.query.get_or_404(id)
    
    if sale.payment_status != 'pending':
        flash('Seules les ventes non payées peuvent être supprimées', 'danger')
        return redirect(url_for('sales.view', id=id))
    
    try:
        delete_reason = request.form.get('delete_reason', 'Suppression de vente')
        
        for item in sale.items:
            product = Product.query.get(item.product_id)
            if product:
                product.stock_quantity += item.quantity
        
        audit = Audit(
            user_id=current_user.id,
            action='delete_sale',
            description=f'Suppression de la vente {sale.invoice_number}. Montant: ${sale.total_amount:.2f}. Raison: {delete_reason}',
            ip_address=request.remote_addr
        )
        db.session.add(audit)
        
        db.session.delete(sale)
        db.session.commit()
        
        flash('Vente supprimée avec succès', 'success')
        return redirect(url_for('sales.index'))
        
    except Exception as e:
        db.session.rollback()
        flash(f'Erreur: {str(e)}', 'danger')
        return redirect(url_for('sales.view', id=id))

@sales_bp.route('/temp/<int:id>/validate', methods=['POST'])
@login_required
@require_permission('manage_cashier')
def validate_temp_sale(id):
    temp_sale = TempSale.query.get_or_404(id)
    
    if temp_sale.status != 'pending':
        return jsonify({'success': False, 'message': 'Vente déjà traitée'}), 400
    
    try:
        items_data = json.loads(temp_sale.items_data)
        
        # Vérifier stock
        for item_data in items_data:
            product = Product.query.get(item_data['product_id'])
            if not product or product.stock_quantity < item_data['quantity']:
                return jsonify({'success': False, 'message': f'Stock insuffisant'}), 400
        
        # Créer la vente finale
        from app.routes.pos import generate_invoice_number
        invoice_number = generate_invoice_number()
        
        sale = Sale(
            invoice_number=invoice_number,
            customer_id=temp_sale.customer_id,
            user_id=temp_sale.created_by,
            pharmacy_id=temp_sale.pharmacy_id,
            discount=temp_sale.discount,
            payment_method=temp_sale.payment_method,
            notes=temp_sale.notes,
            total_amount=temp_sale.total_amount,
            paid_amount=temp_sale.total_amount,
            payment_status='paid',
            payment_type='cash'
        )
        
        db.session.add(sale)
        db.session.flush()
        
        # Créer items et déduire stock
        for item_data in items_data:
            product = Product.query.get(item_data['product_id'])
            
            sale_item = SaleItem(
                sale_id=sale.id,
                product_id=product.id,
                quantity=item_data['quantity'],
                unit_price=item_data['price'],
                total=item_data['quantity'] * item_data['price']
            )
            db.session.add(sale_item)
            
            product.stock_quantity -= item_data['quantity']
            
            movement = StockMovement(
                product_id=product.id,
                movement_type='out',
                quantity=item_data['quantity'],
                reference=invoice_number,
                notes=f'Vente validée {invoice_number}',
                created_by=current_user.id,
                pharmacy_id=temp_sale.pharmacy_id
            )
            db.session.add(movement)
        
        # Paiement
        payment = Payment(
            sale_id=sale.id,
            customer_id=temp_sale.customer_id,
            amount=temp_sale.total_amount,
            payment_method=temp_sale.payment_method
        )
        db.session.add(payment)
        
        # Mettre à jour temp_sale
        temp_sale.status = 'validated'
        temp_sale.validated_by = current_user.id
        temp_sale.validated_at = datetime.utcnow()
        temp_sale.sale_id = sale.id
        
        db.session.commit()
        
        return jsonify({'success': True, 'message': f'Vente validée: {invoice_number}', 'invoice_number': invoice_number})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@sales_bp.route('/temp/<int:id>/reject', methods=['POST'])
@login_required
@require_permission('manage_cashier')
def reject_temp_sale(id):
    temp_sale = TempSale.query.get_or_404(id)
    
    if temp_sale.status != 'pending':
        return jsonify({'success': False, 'message': 'Vente déjà traitée'}), 400
    
    try:
        data = request.get_json()
        rejection_reason = data.get('reason', 'Aucune raison fournie')
        
        temp_sale.status = 'rejected'
        temp_sale.validated_by = current_user.id
        temp_sale.validated_at = datetime.utcnow()
        temp_sale.rejection_reason = rejection_reason
        
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Vente rejetée'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

# ==================== ROUTES PROFORMA ====================

def generate_proforma_number():
    year = datetime.now().year
    count = Proforma.query.filter(
        db.extract('year', Proforma.issue_date) == year
    ).count() + 1
    return f'PROFORMA-{year}-{str(count).zfill(3)}'

@sales_bp.route('/proforma/')
@require_permission('manage_sales')
def proforma_index():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    status = request.args.get('status', '')
    
    query = Proforma.query
    
    if search:
        query = query.filter(
            db.or_(
                Proforma.proforma_number.ilike(f'%{search}%'),
                Proforma.customer_name.ilike(f'%{search}%')
            )
        )
    
    if status:
        query = query.filter_by(status=status)
    
    proformas = query.order_by(Proforma.issue_date.desc()).paginate(
        page=page, per_page=6, error_out=False
    )
    
    return render_template('sales/proforma/index.html', proformas=proformas, search=search, status=status)

@sales_bp.route('/proforma/create', methods=['GET', 'POST'])
@require_permission('manage_sales')
def proforma_create():
    if request.method == 'POST':
        try:
            proforma_number = generate_proforma_number()
            
            validity_date_str = request.form.get('validity_date')
            if not validity_date_str:
                validity_date = (datetime.now() + timedelta(days=30)).date()
            else:
                validity_date = datetime.strptime(validity_date_str, '%Y-%m-%d').date()
            
            proforma = Proforma(
                proforma_number=proforma_number,
                customer_id=request.form.get('customer_id') if request.form.get('customer_id') else None,
                user_id=current_user.id,
                customer_name=request.form.get('customer_name'),
                customer_address=request.form.get('customer_address'),
                customer_phone=request.form.get('customer_phone'),
                customer_email=request.form.get('customer_email'),
                validity_date=validity_date,
                payment_conditions=request.form.get('payment_conditions', 'Paiement à la livraison'),
                delivery_conditions=request.form.get('delivery_conditions', 'Retrait en magasin'),
                notes=request.form.get('notes'),
                status='draft'
            )
            
            product_ids = request.form.getlist('product_id[]')
            quantities = request.form.getlist('quantity[]')
            prices = request.form.getlist('price[]')
            
            if not product_ids or not quantities:
                flash('Veuillez ajouter au moins un produit', 'danger')
                return redirect(url_for('sales.proforma_create'))
            
            total_ht = 0
            for i in range(len(product_ids)):
                if product_ids[i] and quantities[i]:
                    product = Product.query.get(int(product_ids[i]))
                    if product:
                        quantity = int(quantities[i])
                        price = float(prices[i]) if prices[i] else product.selling_price
                        line_total = quantity * price
                        total_ht += line_total
                        
                        item = ProformaItem(
                            product_id=product.id,
                            product_name=product.name,
                            product_code=product.barcode or '',
                            quantity_requested=quantity,
                            stock_available=product.stock_quantity,
                            unit_price=price,
                            line_total=line_total,
                            line_notes=request.form.getlist('line_notes[]')[i] if i < len(request.form.getlist('line_notes[]')) else ''
                        )
                        proforma.items.append(item)
            
            proforma.total_ht = total_ht
            proforma.total_tax = 0.0
            proforma.total_ttc = total_ht
            
            db.session.add(proforma)
            db.session.flush()
            
            audit = Audit(
                user_id=current_user.id,
                action='create_proforma',
                entity_type='proforma',
                entity_id=proforma.id,
                details=f'Proforma créée: {proforma.proforma_number}',
                ip_address=request.remote_addr
            )
            db.session.add(audit)
            
            db.session.commit()
            
            flash('Facture proforma créée avec succès!', 'success')
            return redirect(url_for('sales.proforma_show', id=proforma.id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Erreur: {str(e)}', 'danger')
            return redirect(url_for('sales.proforma_create'))
    
    customers = Customer.query.filter_by(is_active=True).all()
    products = Product.query.filter_by(is_active=True).all()
    default_validity_date = (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')
    
    return render_template('sales/proforma/create.html', customers=customers, products=products, default_validity_date=default_validity_date)

@sales_bp.route('/proforma/show/<int:id>')
@require_permission('manage_sales')
def proforma_show(id):
    proforma = Proforma.query.get_or_404(id)
    return render_template('sales/proforma/show.html', proforma=proforma)

@sales_bp.route('/proforma/edit/<int:id>', methods=['GET', 'POST'])
@require_permission('manage_sales')
def proforma_edit(id):
    proforma = Proforma.query.get_or_404(id)
    
    if request.method == 'POST':
        try:
            validity_date_str = request.form.get('validity_date')
            if validity_date_str:
                proforma.validity_date = datetime.strptime(validity_date_str, '%Y-%m-%d').date()
            
            proforma.customer_id = request.form.get('customer_id') if request.form.get('customer_id') else None
            proforma.customer_name = request.form.get('customer_name')
            proforma.customer_address = request.form.get('customer_address')
            proforma.customer_phone = request.form.get('customer_phone')
            proforma.customer_email = request.form.get('customer_email')
            proforma.payment_conditions = request.form.get('payment_conditions')
            proforma.delivery_conditions = request.form.get('delivery_conditions')
            proforma.notes = request.form.get('notes')
            proforma.status = request.form.get('status', 'draft')
            
            ProformaItem.query.filter_by(proforma_id=id).delete()
            
            product_ids = request.form.getlist('product_id[]')
            quantities = request.form.getlist('quantity[]')
            prices = request.form.getlist('price[]')
            
            total_ht = 0
            for i in range(len(product_ids)):
                if product_ids[i] and quantities[i]:
                    product = Product.query.get(int(product_ids[i]))
                    if product:
                        quantity = int(quantities[i])
                        price = float(prices[i]) if prices[i] else product.selling_price
                        line_total = quantity * price
                        total_ht += line_total
                        
                        item = ProformaItem(
                            proforma_id=proforma.id,
                            product_id=product.id,
                            product_name=product.name,
                            product_code=product.barcode or '',
                            quantity_requested=quantity,
                            stock_available=product.stock_quantity,
                            unit_price=price,
                            line_total=line_total,
                            line_notes=request.form.getlist('line_notes[]')[i] if i < len(request.form.getlist('line_notes[]')) else ''
                        )
                        db.session.add(item)
            
            proforma.total_ht = total_ht
            proforma.total_tax = 0.0
            proforma.total_ttc = total_ht
            
            audit = Audit(
                user_id=current_user.id,
                action='update_proforma',
                entity_type='proforma',
                entity_id=proforma.id,
                details=f'Proforma modifiée: {proforma.proforma_number}',
                ip_address=request.remote_addr
            )
            db.session.add(audit)
            
            db.session.commit()
            
            flash('Facture proforma modifiée avec succès!', 'success')
            return redirect(url_for('sales.proforma_show', id=proforma.id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Erreur: {str(e)}', 'danger')
    
    customers = Customer.query.filter_by(is_active=True).all()
    products = Product.query.filter_by(is_active=True).all()
    
    return render_template('sales/proforma/edit.html', proforma=proforma, customers=customers, products=products)

@sales_bp.route('/proforma/delete/<int:id>', methods=['POST'])
@require_permission('manage_sales')
def proforma_delete(id):
    proforma = Proforma.query.get_or_404(id)
    
    try:
        audit = Audit(
            user_id=current_user.id,
            action='delete_proforma',
            entity_type='proforma',
            entity_id=proforma.id,
            details=f'Proforma supprimée: {proforma.proforma_number}',
            ip_address=request.remote_addr
        )
        db.session.add(audit)
        
        db.session.delete(proforma)
        db.session.commit()
        
        flash('Facture proforma supprimée avec succès!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erreur: {str(e)}', 'danger')
    
    return redirect(url_for('sales.proforma_index'))

@sales_bp.route('/proforma/send/<int:id>', methods=['POST'])
@require_permission('manage_sales')
def proforma_send(id):
    proforma = Proforma.query.get_or_404(id)
    
    try:
        proforma.status = 'sent'
        
        audit = Audit(
            user_id=current_user.id,
            action='send_proforma',
            entity_type='proforma',
            entity_id=proforma.id,
            details=f'Proforma envoyée: {proforma.proforma_number}',
            ip_address=request.remote_addr
        )
        db.session.add(audit)
        
        db.session.commit()
        
        flash('Facture proforma envoyée au client!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erreur: {str(e)}', 'danger')
    
    return redirect(url_for('sales.proforma_show', id=id))

@sales_bp.route('/proforma/print/<int:id>')
@require_permission('manage_sales')
def proforma_print(id):
    proforma = Proforma.query.get_or_404(id)
    return render_template('sales/proforma/print.html', proforma=proforma)

@sales_bp.route('/proforma/convert-to-sale/<int:id>', methods=['POST'])
@require_permission('manage_sales')
def proforma_convert_to_sale(id):
    proforma = Proforma.query.get_or_404(id)
    
    try:
        from app.models import Sale, SaleItem
        
        invoice_number = f'INV-{datetime.now().strftime("%Y%m%d")}-{random.randint(1000, 9999)}'
        
        sale = Sale(
            invoice_number=invoice_number,
            customer_id=proforma.customer_id,
            user_id=current_user.id,
            total_amount=proforma.total_ttc,
            discount=0,
            tax=proforma.total_tax,
            paid_amount=0,
            payment_status='pending',
            notes=f'Convertie depuis proforma {proforma.proforma_number}'
        )
        
        for item in proforma.items:
            sale_item = SaleItem(
                product_id=item.product_id,
                quantity=item.quantity_requested,
                unit_price=item.unit_price,
                total=item.line_total
            )
            sale.items.append(sale_item)
        
        proforma.status = 'accepted'
        
        db.session.add(sale)
        db.session.commit()
        
        flash(f'Proforma convertie en vente {invoice_number}!', 'success')
        return redirect(url_for('sales.view', id=sale.id))
        
    except Exception as e:
        db.session.rollback()
        flash(f'Erreur lors de la conversion: {str(e)}', 'danger')
        return redirect(url_for('sales.proforma_show', id=id))

@sales_bp.route('/proforma/search-products')
@require_permission('manage_sales')
def proforma_search_products():
    query = request.args.get('q', '')
    if len(query) < 2:
        return jsonify([])
    
    products = Product.query.filter(
        Product.is_active == True,
        db.or_(
            Product.name.ilike(f'%{query}%'),
            Product.barcode.ilike(f'%{query}%')
        )
    ).limit(20).all()
    
    return jsonify([{
        'id': p.id,
        'name': p.name,
        'code': p.barcode or '',
        'stock': p.stock_quantity,
        'price': p.selling_price
    } for p in products])

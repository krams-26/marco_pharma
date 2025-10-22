from app import create_app
from app.models import (db, User, Product, Customer, Sale, SaleItem, Payment, 
                        Employee, StockMovement, CashTransaction, ExchangeRate,
                        Pharmacy, UserPharmacy, ProductBatch, Setting)
from datetime import datetime, date, timedelta
import random

app = create_app()

def seed_database():
    with app.app_context():
        print("Début de l'ajout des données de test...")
        
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            print("Erreur: Utilisateur admin introuvable. Veuillez démarrer l'application une fois.")
            return
        
        central_pharmacy = Pharmacy.query.filter_by(type='depot').first()
        if not central_pharmacy:
            print("Erreur: Pharmacie centrale introuvable.")
            return
        
        pharmacies_data = [
            {
                'name': 'Pharmacie MARCOPHAR Nord',
                'type': 'pharmacy',
                'code': 'PHARMA-NORD-002',
                'address': 'Avenue de la Paix, Kinshasa',
                'phone': '+243 800 123 456',
                'email': 'nord@marcophar.com',
                'manager_name': 'Dr. Jean Mukendi',
                'status': 'active',
                'is_active': True,
                'revenue_target': 30000.0
            },
            {
                'name': 'Pharmacie MARCOPHAR Sud',
                'type': 'pharmacy',
                'code': 'PHARMA-SUD-003',
                'address': 'Boulevard Lumumba, Kinshasa',
                'phone': '+243 800 123 457',
                'email': 'sud@marcophar.com',
                'manager_name': 'Dr. Marie Kabongo',
                'status': 'active',
                'is_active': True,
                'revenue_target': 25000.0
            },
            {
                'name': 'Pharmacie MARCOPHAR Est',
                'type': 'pharmacy',
                'code': 'PHARMA-EST-004',
                'address': 'Avenue Mobutu, Lubumbashi',
                'phone': '+243 800 123 458',
                'email': 'est@marcophar.com',
                'manager_name': 'Dr. Paul Tshisekedi',
                'status': 'active',
                'is_active': True,
                'revenue_target': 20000.0
            }
        ]
        
        pharmacies = []
        for pharma_data in pharmacies_data:
            pharma = Pharmacy.query.filter_by(code=pharma_data['code']).first()
            if not pharma:
                pharma = Pharmacy(**pharma_data)
                db.session.add(pharma)
                print(f"Pharmacie ajoutée: {pharma_data['name']}")
            pharmacies.append(pharma)
        
        db.session.commit()
        
        users_data = [
            {
                'username': 'vendeur1',
                'email': 'vendeur1@pharmacy.com',
                'password': 'vendeur123',
                'first_name': 'Jacques',
                'last_name': 'Mulamba',
                'phone': '+243 800 111 111',
                'role': 'vendeur',
                'permissions': {
                    'view_dashboard': True,
                    'manage_sales': True,
                    'view_reports': True
                }
            },
            {
                'username': 'vendeur2',
                'email': 'vendeur2@pharmacy.com',
                'password': 'vendeur123',
                'first_name': 'Sophie',
                'last_name': 'Kasongo',
                'phone': '+243 800 111 112',
                'role': 'vendeur',
                'permissions': {
                    'view_dashboard': True,
                    'manage_sales': True,
                    'view_reports': True
                }
            },
            {
                'username': 'gestionnaire',
                'email': 'manager@pharmacy.com',
                'password': 'manager123',
                'first_name': 'Laurent',
                'last_name': 'Kabila',
                'phone': '+243 800 111 113',
                'role': 'gestionnaire',
                'permissions': {
                    'view_dashboard': True,
                    'manage_products': True,
                    'manage_sales': True,
                    'manage_customers': True,
                    'manage_stock': True,
                    'view_reports': True,
                    'manage_payments': True
                }
            },
            {
                'username': 'pharmacien',
                'email': 'pharmacien@pharmacy.com',
                'password': 'pharma123',
                'first_name': 'Dr. Christine',
                'last_name': 'Mbuyi',
                'phone': '+243 800 111 114',
                'role': 'pharmacien',
                'permissions': {
                    'view_dashboard': True,
                    'manage_products': True,
                    'manage_sales': True,
                    'manage_customers': True,
                    'manage_stock': True,
                    'view_reports': True
                }
            }
        ]
        
        created_users = []
        for user_data in users_data:
            user = User.query.filter_by(username=user_data['username']).first()
            if not user:
                password = user_data.pop('password')
                perms = user_data.pop('permissions')
                user = User(**user_data)
                user.set_password(password)
                user.set_permissions(perms)
                db.session.add(user)
                db.session.flush()
                
                user_pharma = UserPharmacy(
                    user_id=user.id,
                    pharmacy_id=pharmacies[0].id if pharmacies else central_pharmacy.id,
                    is_primary=True,
                    assigned_by=admin.id
                )
                db.session.add(user_pharma)
                print(f"Utilisateur ajouté: {user.username}")
            created_users.append(user)
        
        db.session.commit()
        
        categories = ['Analgésiques', 'Antibiotiques', 'Antipaludéens', 'Antihypertenseurs', 
                     'Vitamines', 'Antiseptiques', 'Anti-inflammatoires', 'Antidiabétiques']
        
        products_data = [
            {'name': 'Paracétamol 500mg', 'category': 'Comprimé', 'barcode': 'PARA500', 
             'purchase_price': 0.5, 'selling_price': 1.0, 'wholesale_price': 0.8, 'stock': 500},
            {'name': 'Amoxicilline 500mg', 'category': 'Gélule', 'barcode': 'AMOX500',
             'purchase_price': 2.0, 'selling_price': 3.5, 'wholesale_price': 3.0, 'stock': 300},
            {'name': 'Quinine 300mg', 'category': 'Comprimé', 'barcode': 'QUIN300',
             'purchase_price': 1.5, 'selling_price': 2.5, 'wholesale_price': 2.2, 'stock': 200},
            {'name': 'Amlodipine 5mg', 'category': 'Comprimé', 'barcode': 'AMLO5',
             'purchase_price': 3.0, 'selling_price': 5.0, 'wholesale_price': 4.5, 'stock': 150},
            {'name': 'Aspirine 100mg', 'category': 'Comprimé', 'barcode': 'ASPI100',
             'purchase_price': 0.3, 'selling_price': 0.7, 'wholesale_price': 0.5, 'stock': 600},
            {'name': 'Ciprofloxacine 500mg', 'category': 'Comprimé', 'barcode': 'CIPRO500',
             'purchase_price': 4.0, 'selling_price': 7.0, 'wholesale_price': 6.0, 'stock': 100},
            {'name': 'Artéméther-Luméfantrine', 'category': 'Comprimé', 'barcode': 'ARTE20',
             'purchase_price': 5.0, 'selling_price': 8.0, 'wholesale_price': 7.0, 'stock': 250},
            {'name': 'Metformine 850mg', 'category': 'Comprimé', 'barcode': 'METF850',
             'purchase_price': 2.5, 'selling_price': 4.0, 'wholesale_price': 3.5, 'stock': 180},
            {'name': 'Ibuprofène 400mg', 'category': 'Comprimé', 'barcode': 'IBUP400',
             'purchase_price': 1.0, 'selling_price': 2.0, 'wholesale_price': 1.7, 'stock': 400},
            {'name': 'Complexe Vitamine B', 'category': 'Capsule', 'barcode': 'VITB',
             'purchase_price': 3.5, 'selling_price': 6.0, 'wholesale_price': 5.0, 'stock': 120},
            {'name': 'Vitamine C 1000mg', 'category': 'Comprimé', 'barcode': 'VITC1000',
             'purchase_price': 2.0, 'selling_price': 3.5, 'wholesale_price': 3.0, 'stock': 200},
            {'name': 'Alcool 70%', 'category': 'Solution', 'barcode': 'ALC70',
             'purchase_price': 1.5, 'selling_price': 2.5, 'wholesale_price': 2.0, 'stock': 150},
            {'name': 'Bétadine Solution', 'category': 'Solution', 'barcode': 'BETA',
             'purchase_price': 3.0, 'selling_price': 5.0, 'wholesale_price': 4.5, 'stock': 80},
            {'name': 'Diclofénac 50mg', 'category': 'Comprimé', 'barcode': 'DICLO50',
             'purchase_price': 1.2, 'selling_price': 2.3, 'wholesale_price': 2.0, 'stock': 220},
            {'name': 'Oméprazole 20mg', 'category': 'Gélule', 'barcode': 'OMEP20',
             'purchase_price': 2.8, 'selling_price': 4.5, 'wholesale_price': 4.0, 'stock': 160}
        ]
        
        for prod_data in products_data:
            product = Product.query.filter_by(barcode=prod_data['barcode']).first()
            if not product:
                product = Product(
                    name=prod_data['name'],
                    category=prod_data['category'],
                    barcode=prod_data['barcode'],
                    purchase_price=prod_data['purchase_price'],
                    selling_price=prod_data['selling_price'],
                    wholesale_price=prod_data['wholesale_price'],
                    stock_quantity=prod_data['stock'],
                    min_stock_level=random.randint(10, 30),
                    unit='boîte',
                    pharmacy_id=central_pharmacy.id,
                    manufacturer='Pharma Industries',
                    supplier='Fournisseur Global',
                    expiry_date=date.today() + timedelta(days=random.randint(180, 730))
                )
                db.session.add(product)
                print(f"Produit ajouté: {prod_data['name']}")
        
        db.session.commit()
        
        customers_data = [
            {'name': 'Hôpital Général de Kinshasa', 'type': 'wholesale', 'credit_limit': 50000},
            {'name': 'Clinique Saint-Luc', 'type': 'wholesale', 'credit_limit': 30000},
            {'name': 'Centre Médical Espoir', 'type': 'wholesale', 'credit_limit': 20000},
            {'name': 'Mutuale de Santé SONAS', 'type': 'wholesale', 'credit_limit': 40000},
            {'name': 'Jean-Pierre Mbala', 'type': 'regular', 'credit_limit': 500},
            {'name': 'Marie-Claire Nkumu', 'type': 'regular', 'credit_limit': 300},
            {'name': 'Joseph Kambale', 'type': 'regular', 'credit_limit': 1000},
            {'name': 'Grace Lumumba', 'type': 'vip', 'credit_limit': 5000},
        ]
        
        created_customers = []
        for i, cust_data in enumerate(customers_data):
            customer = Customer.query.filter_by(name=cust_data['name']).first()
            if not customer:
                customer = Customer(
                    name=cust_data['name'],
                    email=f"client{i+1}@example.com",
                    phone=f"+243 800 20{i+1:04d}",
                    address=f"Adresse {i+1}, Kinshasa",
                    customer_type=cust_data['type'],
                    credit_limit=cust_data['credit_limit'],
                    current_credit=0.0
                )
                db.session.add(customer)
                print(f"Client ajouté: {cust_data['name']}")
            created_customers.append(customer)
        
        db.session.commit()
        
        for i, user_data in enumerate(users_data[:2]):
            employee = Employee.query.filter_by(employee_id=f'EMP-{i+1:03d}').first()
            if not employee:
                user = User.query.filter_by(username=user_data['username']).first()
                if user:
                    employee = Employee(
                        user_id=user.id,
                        employee_id=f'EMP-{i+1:03d}',
                        position='Vendeur',
                        department='Ventes',
                        salary=800.0,
                        hire_date=date.today() - timedelta(days=random.randint(30, 365))
                    )
                    db.session.add(employee)
                    print(f"Employé ajouté: {user.full_name}")
        
        db.session.commit()
        
        products = Product.query.limit(10).all()
        for i in range(5):
            invoice_num = f'INV-{datetime.now().strftime("%Y%m%d")}-{i+1:04d}'
            existing_sale = Sale.query.filter_by(invoice_number=invoice_num).first()
            if not existing_sale:
                customer = random.choice(created_customers)
                seller = random.choice([admin] + created_users)
                
                sale = Sale(
                    invoice_number=invoice_num,
                    customer_id=customer.id,
                    user_id=seller.id,
                    pharmacy_id=central_pharmacy.id,
                    payment_status='paid',
                    payment_method='cash',
                    sale_date=datetime.now() - timedelta(days=random.randint(0, 30))
                )
                
                total = 0
                num_items = random.randint(2, 5)
                selected_products = random.sample(products, min(num_items, len(products)))
                
                for product in selected_products:
                    quantity = random.randint(1, 10)
                    unit_price = product.selling_price if customer.customer_type == 'regular' else product.wholesale_price
                    item_total = quantity * unit_price
                    
                    sale_item = SaleItem(
                        product_id=product.id,
                        quantity=quantity,
                        unit_price=unit_price,
                        total=item_total
                    )
                    sale.items.append(sale_item)
                    total += item_total
                
                sale.total_amount = total
                sale.paid_amount = total
                
                db.session.add(sale)
                print(f"Vente ajoutée: {invoice_num}")
        
        db.session.commit()
        
        transaction_types = [
            ('income', 'Vente au comptant', 150.0),
            ('income', 'Paiement client', 500.0),
            ('expense', 'Achat fournitures', -80.0),
            ('income', 'Vente médicaments', 220.0),
            ('expense', 'Électricité', -120.0),
            ('income', 'Vente au comptant', 95.0),
            ('expense', 'Salaire vendeur', -300.0),
        ]
        
        for trans_type, desc, amount in transaction_types:
            transaction = CashTransaction(
                transaction_type=trans_type,
                amount=abs(amount),
                description=desc,
                reference=f'REF-{datetime.now().strftime("%Y%m%d")}-{random.randint(1000, 9999)}',
                created_by=admin.id,
                created_at=datetime.now() - timedelta(days=random.randint(0, 15))
            )
            db.session.add(transaction)
        
        print("Transactions de caisse ajoutées")
        db.session.commit()
        
        exchange_rates_data = [
            {'from_currency': 'USD', 'to_currency': 'CDF', 'rate': 2800.0},
            {'from_currency': 'EUR', 'to_currency': 'CDF', 'rate': 3100.0},
            {'from_currency': 'EUR', 'to_currency': 'USD', 'rate': 1.1},
        ]
        
        for rate_data in exchange_rates_data:
            rate = ExchangeRate.query.filter_by(
                from_currency=rate_data['from_currency'],
                to_currency=rate_data['to_currency']
            ).first()
            
            if not rate:
                rate = ExchangeRate(**rate_data)
                db.session.add(rate)
            else:
                rate.rate = rate_data['rate']
                rate.updated_at = datetime.utcnow()
        
        print("Taux de change ajoutés/mis à jour")
        db.session.commit()
        
        print("\n[OK] Donnees de test ajoutees avec succes!")
        print("\nInformations de connexion:")
        print("=" * 50)
        print("Admin:")
        print("  Username: admin")
        print("  Password: admin123")
        print("\nVendeur:")
        print("  Username: vendeur1")
        print("  Password: vendeur123")
        print("\nGestionnaire:")
        print("  Username: gestionnaire")
        print("  Password: manager123")
        print("\nPharmacien:")
        print("  Username: pharmacien")
        print("  Password: pharma123")
        print("=" * 50)

if __name__ == '__main__':
    seed_database()


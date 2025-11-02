from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
import json

db = SQLAlchemy()

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    first_name = db.Column(db.String(100))
    last_name = db.Column(db.String(100))
    phone = db.Column(db.String(20))
    role = db.Column(db.String(20), default='vendeur')
    permissions = db.Column(db.Text, default='{}')
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    sales = db.relationship('Sale', foreign_keys='Sale.user_id', backref='seller', lazy=True)
    audits = db.relationship('Audit', backref='user', lazy=True)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def get_permissions(self):
        return json.loads(self.permissions) if self.permissions else {}
    
    def set_permissions(self, perms_dict):
        self.permissions = json.dumps(perms_dict)
    
    def has_permission(self, permission):
        # Les administrateurs ont accès à toutes les permissions
        if self.role == 'admin':
            return True
        
        perms = self.get_permissions()
        
        # Vérification directe
        if perms.get(permission, False):
            return True
        
        # Mapping de compatibilité pour anciennes permissions
        permission_mapping = {
            'view_dashboard': ['dashboard_stats', 'products_view', 'sales_view', 'customers_view', 'reports_view'],
            'manage_products': ['products_view', 'products_create', 'products_edit', 'products_delete'],
            'manage_sales': ['sales_view', 'sales_create', 'sales_edit', 'sales_delete', 'sales_print', 'sales_validate'],
            'manage_customers': ['customers_view', 'customers_create', 'customers_edit', 'customers_delete'],
            'manage_users': ['users_view', 'users_create', 'users_edit', 'users_delete', 'users_permissions'],
            'manage_stock': ['stock_view', 'stock_movements', 'stock_adjust', 'stock_transfer', 'stock_lots'],
            'manage_hr': ['hr_view', 'hr_create', 'hr_edit', 'hr_delete', 'hr_salaries', 'evaluations_view'],
            'manage_payments': ['payments_view', 'payments_create', 'payments_edit'],
            'manage_cashier': ['cashier_access', 'cashier_open', 'cashier_close', 'cashier_view_history', 'sales_validate', 'sales_view'],
            'view_reports': ['reports_view', 'reports_sales', 'reports_stock', 'reports_products'],
            'view_audits': ['audits_view'],
            'manage_settings': ['settings_view', 'settings_edit', 'settings_exchange_rates', 'pharmacies_view', 'pharmacies_create', 'validation_request'],
            'view_tasks': ['tasks_view'],
            'create_task': ['tasks_create'],
            'edit_task': ['tasks_edit'],
            'delete_task': ['tasks_delete'],
            'view_approvals': ['approvals_view'],
            'approve_requests': ['approvals_approve', 'approvals_reject'],
            'manage_suppliers': ['suppliers_view', 'suppliers_create', 'suppliers_edit', 'suppliers_delete'],
            'edit_sales': ['sales_edit'],
            'delete_sales': ['sales_delete'],
        }
        
        # Si c'est une ancienne permission, vérifier si l'utilisateur a l'une des nouvelles permissions correspondantes
        if permission in permission_mapping:
            for new_perm in permission_mapping[permission]:
                if perms.get(new_perm, False):
                    return True
        
        return False
    
    @property
    def full_name(self):
        return f"{self.first_name or ''} {self.last_name or ''}".strip()
    
    @property
    def primary_pharmacy(self):
        """Obtenir la pharmacie principale de l'utilisateur (propriété)"""
        assignment = UserPharmacy.query.filter_by(user_id=self.id, is_primary=True).first()
        if assignment and assignment.pharmacy:
            return assignment.pharmacy
        return None
    
    def get_primary_pharmacy(self):
        """Obtenir la pharmacie principale de l'utilisateur (méthode)"""
        assignment = UserPharmacy.query.filter_by(user_id=self.id, is_primary=True).first()
        if assignment and assignment.pharmacy:
            return assignment.pharmacy
        return None
    
    def get_all_pharmacies(self):
        """Obtenir toutes les pharmacies de l'utilisateur"""
        return [assignment.pharmacy for assignment in self.pharmacy_assignments]
    
    def has_pharmacy_access(self, pharmacy_id):
        """Vérifier si l'utilisateur a accès à une pharmacie"""
        return UserPharmacy.query.filter_by(user_id=self.id, pharmacy_id=pharmacy_id).first() is not None

class Product(db.Model):
    __tablename__ = 'products'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False, index=True)
    description = db.Column(db.Text)
    barcode = db.Column(db.String(100), unique=True, index=True)
    category = db.Column(db.String(100))
    unit = db.Column(db.String(50), default='piece')
    purchase_price = db.Column(db.Float, default=0.0)
    selling_price = db.Column(db.Float, default=0.0)
    wholesale_price = db.Column(db.Float, default=0.0)
    stock_quantity = db.Column(db.Integer, default=0)
    min_stock_level = db.Column(db.Integer, default=10)
    expiry_date = db.Column(db.Date)
    manufacturer = db.Column(db.String(200))
    supplier = db.Column(db.String(200))
    supplier_id = db.Column(db.Integer, db.ForeignKey('suppliers.id'))
    pharmacy_id = db.Column(db.Integer, db.ForeignKey('pharmacies.id'))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    stock_movements = db.relationship('StockMovement', backref='product', lazy=True)
    sale_items = db.relationship('SaleItem', backref='product', lazy=True)
    batches = db.relationship('ProductBatch', backref='product', lazy=True)
    
    @property
    def is_low_stock(self):
        return self.stock_quantity <= self.min_stock_level
    
    @property
    def is_expired(self):
        if self.expiry_date:
            return self.expiry_date < datetime.now().date()
        return False

class ProductBatch(db.Model):
    __tablename__ = 'product_batches'
    
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    pharmacy_id = db.Column(db.Integer, db.ForeignKey('pharmacies.id'))
    batch_number = db.Column(db.String(100), nullable=False, index=True)
    quantity = db.Column(db.Integer, nullable=False)
    initial_quantity = db.Column(db.Integer, nullable=False)
    purchase_price = db.Column(db.Float, nullable=False)
    unit_cost = db.Column(db.Float)
    manufacture_date = db.Column(db.Date)
    expiry_date = db.Column(db.Date, index=True)
    received_date = db.Column(db.DateTime, default=datetime.utcnow)
    supplier_id = db.Column(db.Integer, db.ForeignKey('suppliers.id'))
    supplier = db.Column(db.String(200))
    status = db.Column(db.String(20), default='active')  # active, expired, recalled, depleted
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    pharmacy = db.relationship('Pharmacy', backref='product_batches')
    supplier_rel = db.relationship('Supplier', backref='product_batches')
    movements = db.relationship('BatchMovement', backref='batch', lazy=True, cascade='all, delete-orphan')
    
    @property
    def is_expired(self):
        """Vérifier si le lot est expiré"""
        if self.expiry_date:
            return datetime.now().date() > self.expiry_date
        return False
    
    @property
    def days_until_expiry(self):
        """Nombre de jours avant expiration"""
        if self.expiry_date:
            delta = self.expiry_date - datetime.now().date()
            return delta.days
        return None
    
    @property
    def is_expiring_soon(self):
        """Vérifier si le lot expire bientôt (dans les 90 jours)"""
        days = self.days_until_expiry
        return days is not None and 0 <= days <= 90
    
    def update_status(self):
        """Mettre à jour le statut du lot automatiquement"""
        if self.quantity <= 0:
            self.status = 'depleted'
        elif self.is_expired:
            self.status = 'expired'
        elif not self.is_active:
            self.status = 'recalled'
        else:
            self.status = 'active'


class BatchMovement(db.Model):
    __tablename__ = 'batch_movements'
    
    id = db.Column(db.Integer, primary_key=True)
    batch_id = db.Column(db.Integer, db.ForeignKey('product_batches.id'), nullable=False)
    movement_type = db.Column(db.String(20), nullable=False)  # entry, sale, transfer_in, transfer_out, adjustment, expiry, return
    quantity = db.Column(db.Integer, nullable=False)
    reference_type = db.Column(db.String(50))  # sale, transfer, adjustment, purchase
    reference_id = db.Column(db.Integer)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    user = db.relationship('User', backref='batch_movements')

class Customer(db.Model):
    __tablename__ = 'customers'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False, index=True)
    email = db.Column(db.String(120))
    phone = db.Column(db.String(20))
    address = db.Column(db.Text)
    customer_type = db.Column(db.String(20), default='regular')
    credit_limit = db.Column(db.Float, default=0.0)
    current_credit = db.Column(db.Float, default=0.0)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    sales = db.relationship('Sale', backref='customer', lazy=True)
    payments = db.relationship('Payment', backref='customer', lazy=True)

class Sale(db.Model):
    __tablename__ = 'sales'
    
    id = db.Column(db.Integer, primary_key=True)
    invoice_number = db.Column(db.String(50), unique=True, nullable=False, index=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    pharmacy_id = db.Column(db.Integer, db.ForeignKey('pharmacies.id'))
    total_amount = db.Column(db.Float, default=0.0)
    discount = db.Column(db.Float, default=0.0)
    tax = db.Column(db.Float, default=0.0)
    paid_amount = db.Column(db.Float, default=0.0)
    remaining_amount = db.Column(db.Float, default=0.0)
    payment_status = db.Column(db.String(20), default='pending')
    payment_type = db.Column(db.String(20), default='cash')
    credit_status = db.Column(db.String(20))
    payment_method = db.Column(db.String(50))
    notes = db.Column(db.Text)
    sale_date = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_edited = db.Column(db.Boolean, default=False)
    edited_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    edited_at = db.Column(db.DateTime)
    edit_reason = db.Column(db.Text)
    
    items = db.relationship('SaleItem', backref='sale', lazy=True, cascade='all, delete-orphan')
    editor = db.relationship('User', foreign_keys=[edited_by], backref='sales_edited')
    payments = db.relationship('Payment', backref='sale', lazy=True)
    partial_payments = db.relationship('SalePayment', backref='sale', lazy=True, cascade='all, delete-orphan')
    
    @property
    def balance_due(self):
        """Calcule toujours le solde dû dynamiquement"""
        return max(0, self.total_amount - self.paid_amount)
    
    def calculate_remaining(self):
        """Calculer le montant restant"""
        total_partial = sum(p.amount for p in self.partial_payments if p.status == 'confirmed')
        self.remaining_amount = self.total_amount - total_partial - self.paid_amount
        return self.remaining_amount
    
    def update_credit_status(self):
        """Mettre à jour le statut crédit"""
        if self.payment_type == 'credit':
            if self.remaining_amount <= 0:
                self.credit_status = 'paid'
                self.payment_status = 'paid'
            elif self.paid_amount > 0 or len(self.partial_payments) > 0:
                self.credit_status = 'partially_paid'
                self.payment_status = 'partial'
            else:
                self.credit_status = 'unpaid'
                self.payment_status = 'pending'

class SaleItem(db.Model):
    __tablename__ = 'sale_items'
    
    id = db.Column(db.Integer, primary_key=True)
    sale_id = db.Column(db.Integer, db.ForeignKey('sales.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    unit_price = db.Column(db.Float, nullable=False)
    discount = db.Column(db.Float, default=0.0)
    total = db.Column(db.Float, nullable=False)

class Payment(db.Model):
    __tablename__ = 'payments'
    
    id = db.Column(db.Integer, primary_key=True)
    sale_id = db.Column(db.Integer, db.ForeignKey('sales.id'))
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'))
    amount = db.Column(db.Float, nullable=False)
    payment_method = db.Column(db.String(50), nullable=False)
    reference = db.Column(db.String(100))
    notes = db.Column(db.Text)
    payment_date = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class SalePayment(db.Model):
    __tablename__ = 'sale_payments'
    
    id = db.Column(db.Integer, primary_key=True)
    sale_id = db.Column(db.Integer, db.ForeignKey('sales.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    payment_method = db.Column(db.String(50), default='cash')
    payment_date = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    reference = db.Column(db.String(100))
    notes = db.Column(db.Text)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    status = db.Column(db.String(20), default='confirmed')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    creator = db.relationship('User', foreign_keys=[created_by], backref='sale_payments_created')

class StockMovement(db.Model):
    __tablename__ = 'stock_movements'
    
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    pharmacy_id = db.Column(db.Integer, db.ForeignKey('pharmacies.id'))
    movement_type = db.Column(db.String(20), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    reference = db.Column(db.String(100))
    notes = db.Column(db.Text)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    user = db.relationship('User', foreign_keys=[created_by], backref='stock_movements_created')

class Employee(db.Model):
    __tablename__ = 'employees'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True)
    employee_id = db.Column(db.String(50), unique=True, nullable=False)
    position = db.Column(db.String(100))
    department = db.Column(db.String(100))
    salary = db.Column(db.Float, default=0.0)
    hire_date = db.Column(db.Date)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', backref='employee', uselist=False)
    absences = db.relationship('Absence', backref='employee', lazy=True)
    salary_payments = db.relationship('SalaryPayment', backref='employee', lazy=True)
    leave_requests = db.relationship('LeaveRequest', backref='employee', lazy=True)
    credit_requests = db.relationship('CreditRequest', backref='employee', lazy=True)
    
    @property
    def first_name(self):
        return self.user.first_name if self.user else ''
    
    @property
    def last_name(self):
        return self.user.last_name if self.user else ''
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip()

class Absence(db.Model):
    __tablename__ = 'absences'
    
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=False)
    absence_date = db.Column(db.Date, nullable=False)
    reason = db.Column(db.String(200))
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class SalaryPayment(db.Model):
    __tablename__ = 'salary_payments'
    
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    period = db.Column(db.String(50))
    payment_date = db.Column(db.Date, nullable=False)
    payment_method = db.Column(db.String(50))
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class LeaveRequest(db.Model):
    __tablename__ = 'leave_requests'
    
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    leave_type = db.Column(db.String(50))
    reason = db.Column(db.Text)
    status = db.Column(db.String(20), default='pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class CreditRequest(db.Model):
    __tablename__ = 'credit_requests'
    
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    reason = db.Column(db.Text)
    status = db.Column(db.String(20), default='pending')
    repayment_status = db.Column(db.String(20), default='pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class CashTransaction(db.Model):
    __tablename__ = 'cash_transactions'
    
    id = db.Column(db.Integer, primary_key=True)
    transaction_type = db.Column(db.String(20), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    description = db.Column(db.String(200))
    reference = db.Column(db.String(100))
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

class Expense(db.Model):
    __tablename__ = 'expenses'
    
    id = db.Column(db.Integer, primary_key=True)
    pharmacy_id = db.Column(db.Integer, db.ForeignKey('pharmacies.id'))
    category = db.Column(db.String(100), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    description = db.Column(db.Text)
    expense_date = db.Column(db.Date, nullable=False)
    payment_method = db.Column(db.String(50))
    notes = db.Column(db.Text)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Audit(db.Model):
    __tablename__ = 'audits'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    action = db.Column(db.String(100), nullable=False, index=True)
    entity_type = db.Column(db.String(50))
    entity_id = db.Column(db.Integer)
    details = db.Column(db.Text)
    ip_address = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    # Champs optionnels (ajoutés progressivement)
    module = db.Column(db.String(50), index=True, nullable=True)
    action_type = db.Column(db.String(20), index=True, nullable=True)
    result = db.Column(db.String(20), default='success', nullable=True)
    old_value = db.Column(db.Text, nullable=True)
    new_value = db.Column(db.Text, nullable=True)
    user_agent = db.Column(db.String(255), nullable=True)
    session_id = db.Column(db.String(100), nullable=True)
    
    @property
    def is_suspicious(self):
        """Détecter une activité suspecte"""
        # Échec de connexion
        if self.action_type == 'login' and self.result == 'failed':
            return True
        # Accès refusé
        if self.result == 'denied':
            return True
        # Suppression en masse
        if self.action_type == 'delete' and self.details and 'mass' in self.details.lower():
            return True
        return False
    
    @property
    def has_changes(self):
        """Vérifier si l'audit contient des changements (before/after)"""
        return self.old_value is not None and self.new_value is not None
    
    def get_old_value_dict(self):
        """Récupérer old_value en dict"""
        if self.old_value:
            try:
                return json.loads(self.old_value)
            except:
                return {}
        return {}
    
    def get_new_value_dict(self):
        """Récupérer new_value en dict"""
        if self.new_value:
            try:
                return json.loads(self.new_value)
            except:
                return {}
        return {}
    
    def get_changes(self):
        """Récupérer les changements entre old et new"""
        old = self.get_old_value_dict()
        new = self.get_new_value_dict()
        changes = {}
        
        for key in set(list(old.keys()) + list(new.keys())):
            old_val = old.get(key)
            new_val = new.get(key)
            if old_val != new_val:
                changes[key] = {'old': old_val, 'new': new_val}
        
        return changes

class Setting(db.Model):
    __tablename__ = 'settings'
    
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), unique=True, nullable=False)
    value = db.Column(db.Text)
    description = db.Column(db.String(200))
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class SystemConfig(db.Model):
    """Configuration système de l'application - remplace les valeurs hardcodées de config.py"""
    __tablename__ = 'system_config'
    
    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String(50), nullable=False, index=True)  # company, financial, stock, regional
    key = db.Column(db.String(100), unique=True, nullable=False, index=True)
    value = db.Column(db.Text)
    data_type = db.Column(db.String(20), default='string')  # string, number, boolean, json
    is_active = db.Column(db.Boolean, default=True, index=True)
    description = db.Column(db.Text)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    updated_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    creator = db.relationship('User', foreign_keys=[created_by], backref='configs_created')
    updater = db.relationship('User', foreign_keys=[updated_by], backref='configs_updated')
    
    @staticmethod
    def get(key, default=None):
        """Récupérer une valeur de configuration"""
        config = SystemConfig.query.filter_by(key=key, is_active=True).first()
        if config:
            return config.get_value()
        return default
    
    def get_value(self):
        """Convertir la valeur selon son type"""
        if self.data_type == 'number':
            try:
                if '.' in self.value:
                    return float(self.value)
                return int(self.value)
            except (ValueError, TypeError):
                return 0
        elif self.data_type == 'boolean':
            return self.value.lower() in ('true', '1', 'yes', 'on')
        elif self.data_type == 'json':
            try:
                return json.loads(self.value)
            except:
                return {}
        return self.value
    
    @staticmethod
    def set(key, value, category='general', data_type='string', description=None):
        """Définir une valeur de configuration"""
        config = SystemConfig.query.filter_by(key=key).first()
        if config:
            config.value = str(value)
            config.data_type = data_type
            if description:
                config.description = description
        else:
            config = SystemConfig(
                key=key,
                value=str(value),
                category=category,
                data_type=data_type,
                description=description
            )
            db.session.add(config)
        db.session.commit()
        return config

class ExchangeRate(db.Model):
    __tablename__ = 'exchange_rates'
    
    id = db.Column(db.Integer, primary_key=True)
    from_currency = db.Column(db.String(10), nullable=False)
    to_currency = db.Column(db.String(10), nullable=False)
    rate = db.Column(db.Float, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Proforma(db.Model):
    __tablename__ = 'proformas'
    
    id = db.Column(db.Integer, primary_key=True)
    proforma_number = db.Column(db.String(50), unique=True, nullable=False, index=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    customer_name = db.Column(db.String(200), nullable=False)
    customer_address = db.Column(db.Text)
    customer_phone = db.Column(db.String(20))
    customer_email = db.Column(db.String(120))
    validity_date = db.Column(db.Date, nullable=False)
    total_ht = db.Column(db.Float, default=0.0)
    total_tax = db.Column(db.Float, default=0.0)
    total_ttc = db.Column(db.Float, default=0.0)
    payment_conditions = db.Column(db.Text)
    delivery_conditions = db.Column(db.Text)
    notes = db.Column(db.Text)
    status = db.Column(db.String(20), default='draft')
    issue_date = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    items = db.relationship('ProformaItem', backref='proforma', lazy=True, cascade='all, delete-orphan')
    
    @property
    def is_expired(self):
        if self.validity_date:
            return self.validity_date < datetime.now().date()
        return False

class ProformaItem(db.Model):
    __tablename__ = 'proforma_items'
    
    id = db.Column(db.Integer, primary_key=True)
    proforma_id = db.Column(db.Integer, db.ForeignKey('proformas.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'))
    product_name = db.Column(db.String(200), nullable=False)
    product_code = db.Column(db.String(100))
    quantity_requested = db.Column(db.Integer, nullable=False)
    stock_available = db.Column(db.Integer, default=0)
    unit_price = db.Column(db.Float, nullable=False)
    line_total = db.Column(db.Float, nullable=False)
    line_notes = db.Column(db.Text)

class Pharmacy(db.Model):
    __tablename__ = 'pharmacies'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    type = db.Column(db.String(20), default='pharmacy')
    code = db.Column(db.String(50), unique=True, index=True)
    address = db.Column(db.Text)
    phone = db.Column(db.String(20))
    email = db.Column(db.String(255))
    status = db.Column(db.String(20), default='active')
    manager_name = db.Column(db.String(255))
    license_number = db.Column(db.String(100))
    opening_hours = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    revenue_target = db.Column(db.Float, default=0.0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user_pharmacy_assignments = db.relationship('UserPharmacy', back_populates='pharmacy', lazy=True, cascade='all, delete-orphan')
    products = db.relationship('Product', backref='pharmacy', lazy=True)
    sales = db.relationship('Sale', backref='pharmacy', lazy=True)
    stock_movements = db.relationship('StockMovement', backref='pharmacy', lazy=True, foreign_keys='StockMovement.pharmacy_id')

class UserPharmacy(db.Model):
    __tablename__ = 'user_pharmacies'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    pharmacy_id = db.Column(db.Integer, db.ForeignKey('pharmacies.id'), nullable=False)
    is_primary = db.Column(db.Boolean, default=False)
    assigned_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    assigned_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', foreign_keys=[user_id], backref='pharmacy_assignments')
    pharmacy = db.relationship('Pharmacy', back_populates='user_pharmacy_assignments')
    assigner = db.relationship('User', foreign_keys=[assigned_by])

class Notification(db.Model):
    __tablename__ = 'notifications'
    
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(50), default='system_alert')
    title = db.Column(db.String(255), nullable=False)
    message = db.Column(db.Text, nullable=False)
    requester_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    target_admin_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    status = db.Column(db.String(20), default='pending')
    priority = db.Column(db.String(20), default='medium')
    action_required = db.Column(db.String(100))
    reference_type = db.Column(db.String(50))
    reference_id = db.Column(db.Integer)
    read_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    requester = db.relationship('User', foreign_keys=[requester_id], backref='notifications_sent')
    target_admin = db.relationship('User', foreign_keys=[target_admin_id], backref='notifications_received')

class ValidationCode(db.Model):
    __tablename__ = 'validation_codes'
    
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(8), unique=True, nullable=False, index=True)
    type = db.Column(db.String(50), default='status_change')
    status = db.Column(db.String(20), default='active')
    reference_id = db.Column(db.Integer)
    reference_type = db.Column(db.String(50), default='sale')
    generated_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    generated_for = db.Column(db.Integer, db.ForeignKey('users.id'))
    used_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    used_at = db.Column(db.DateTime)
    expires_at = db.Column(db.DateTime, nullable=False, index=True)
    is_used = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    generator = db.relationship('User', foreign_keys=[generated_by], backref='codes_generated')
    recipient = db.relationship('User', foreign_keys=[generated_for], backref='codes_received')
    user_who_used = db.relationship('User', foreign_keys=[used_by], backref='codes_used')
    
    @property
    def is_expired(self):
        return self.expires_at < datetime.utcnow()
    
    @property
    def is_valid(self):
        return self.status == 'active' and not self.is_used and not self.is_expired

class EmployeeEvaluation(db.Model):
    __tablename__ = 'employee_evaluations'
    
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=False)
    evaluator_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    evaluation_date = db.Column(db.Date, nullable=False)
    period_evaluated = db.Column(db.String(50))
    overall_score = db.Column(db.Float)
    comments = db.Column(db.Text)
    strengths = db.Column(db.Text)
    improvements = db.Column(db.Text)
    future_goals = db.Column(db.Text)
    status = db.Column(db.String(20), default='draft')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    employee = db.relationship('Employee', backref='evaluations')
    evaluator = db.relationship('User', foreign_keys=[evaluator_id], backref='evaluations_made')
    criteria = db.relationship('EvaluationCriteria', backref='evaluation', lazy=True, cascade='all, delete-orphan')

class EvaluationCriteria(db.Model):
    __tablename__ = 'evaluation_criteria'
    
    id = db.Column(db.Integer, primary_key=True)
    evaluation_id = db.Column(db.Integer, db.ForeignKey('employee_evaluations.id'), nullable=False)
    criteria_name = db.Column(db.String(100), nullable=False)
    score = db.Column(db.Float, nullable=False)
    max_score = db.Column(db.Float, default=10.0)
    notes = db.Column(db.Text)

class Task(db.Model):
    __tablename__ = 'tasks'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    assigned_to = db.Column(db.Integer, db.ForeignKey('users.id'))
    assigned_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    pharmacy_id = db.Column(db.Integer, db.ForeignKey('pharmacies.id'))
    priority = db.Column(db.String(20), default='medium')
    status = db.Column(db.String(20), default='pending')
    due_date = db.Column(db.DateTime)
    completed_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    assignee = db.relationship('User', foreign_keys=[assigned_to], backref='tasks_assigned')
    assigner = db.relationship('User', foreign_keys=[assigned_by], backref='tasks_created')
    
    @property
    def is_overdue(self):
        if self.due_date and self.status != 'completed':
            return self.due_date < datetime.utcnow()
        return False

class Approval(db.Model):
    __tablename__ = 'approvals'
    
    id = db.Column(db.Integer, primary_key=True)
    request_type = db.Column(db.String(50), nullable=False)
    entity_type = db.Column(db.String(50))
    entity_id = db.Column(db.Integer)
    requested_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    approver_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    pharmacy_id = db.Column(db.Integer, db.ForeignKey('pharmacies.id'))
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    request_data = db.Column(db.Text)
    status = db.Column(db.String(20), default='pending')
    approval_level = db.Column(db.Integer, default=1)
    priority = db.Column(db.String(20), default='medium')
    approved_at = db.Column(db.DateTime)
    rejected_at = db.Column(db.DateTime)
    rejection_reason = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    requester = db.relationship('User', foreign_keys=[requested_by], backref='approval_requests')
    approver = db.relationship('User', foreign_keys=[approver_id], backref='approvals_to_review')
    
    @property
    def is_pending(self):
        return self.status == 'pending'
    
    @property
    def is_approved(self):
        return self.status == 'approved'
    
    @property
    def is_rejected(self):
        return self.status == 'rejected'

class Supplier(db.Model):
    __tablename__ = 'suppliers'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False, index=True)
    code = db.Column(db.String(50), unique=True, index=True)
    contact_person = db.Column(db.String(200))
    email = db.Column(db.String(200))
    phone = db.Column(db.String(20))
    phone2 = db.Column(db.String(20))
    address = db.Column(db.Text)
    city = db.Column(db.String(100))
    country = db.Column(db.String(100))
    website = db.Column(db.String(255))
    tax_id = db.Column(db.String(100))
    payment_terms = db.Column(db.String(100))
    credit_limit = db.Column(db.Float, default=0.0)
    current_balance = db.Column(db.Float, default=0.0)
    status = db.Column(db.String(20), default='active')
    notes = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    products = db.relationship('Product', backref='supplier_obj', lazy=True)
    
    @property
    def total_products(self):
        return len(self.products)

class SaleCredit(db.Model):
    __tablename__ = 'sale_credits'
    
    id = db.Column(db.Integer, primary_key=True)
    sale_id = db.Column(db.Integer, db.ForeignKey('sales.id'), nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=False)
    pharmacy_id = db.Column(db.Integer, db.ForeignKey('pharmacies.id'))
    credit_amount = db.Column(db.Float, nullable=False)
    paid_amount = db.Column(db.Float, default=0.0)
    remaining_amount = db.Column(db.Float, nullable=False)
    credit_limit_used = db.Column(db.Float, default=0.0)
    interest_rate = db.Column(db.Float, default=0.0)
    credit_days = db.Column(db.Integer, default=30)
    due_date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(20), default='active')  # active, paid, overdue, defaulted
    payment_terms = db.Column(db.Text)
    notes = db.Column(db.Text)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    sale = db.relationship('Sale', backref='credit_record')
    customer = db.relationship('Customer', backref='credit_sales')
    pharmacy = db.relationship('Pharmacy', backref='sale_credits')
    creator = db.relationship('User', backref='sale_credits_created')
    payments = db.relationship('CreditPayment', backref='sale_credit', lazy=True, cascade='all, delete-orphan')
    
    @property
    def is_overdue(self):
        """Vérifier si le crédit est en retard"""
        return self.due_date < datetime.now().date() and self.status == 'active'
    
    @property
    def days_overdue(self):
        """Nombre de jours de retard"""
        if self.is_overdue:
            return (datetime.now().date() - self.due_date).days
        return 0
    
    def calculate_interest(self):
        """Calculer les intérêts si applicable"""
        if self.interest_rate > 0 and self.is_overdue:
            days = self.days_overdue
            return (self.remaining_amount * self.interest_rate / 100) * (days / 30)
        return 0
    
    def update_status(self):
        """Mettre à jour le statut automatiquement"""
        if self.remaining_amount <= 0:
            self.status = 'paid'
        elif self.is_overdue:
            self.status = 'overdue'
        else:
            self.status = 'active'

class CreditPayment(db.Model):
    __tablename__ = 'credit_payments'
    
    id = db.Column(db.Integer, primary_key=True)
    sale_credit_id = db.Column(db.Integer, db.ForeignKey('sale_credits.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    payment_method = db.Column(db.String(50), default='cash')
    payment_date = db.Column(db.Date, nullable=False, index=True)
    reference = db.Column(db.String(100))
    notes = db.Column(db.Text)
    interest_amount = db.Column(db.Float, default=0.0)
    principal_amount = db.Column(db.Float, nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    creator = db.relationship('User', backref='credit_payments_created')
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.principal_amount:
            self.principal_amount = self.amount - (self.interest_amount or 0)

class CreditTerms(db.Model):
    __tablename__ = 'credit_terms'
    
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=False)
    credit_limit = db.Column(db.Float, nullable=False)
    credit_days = db.Column(db.Integer, default=30)
    interest_rate = db.Column(db.Float, default=0.0)
    grace_period_days = db.Column(db.Integer, default=5)
    payment_terms = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    customer = db.relationship('Customer', backref='credit_terms')

class TempSale(db.Model):
    __tablename__ = 'temp_sales'
    
    id = db.Column(db.Integer, primary_key=True)
    reference = db.Column(db.String(50), unique=True, nullable=False, index=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'))
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    pharmacy_id = db.Column(db.Integer, db.ForeignKey('pharmacies.id'))
    total_amount = db.Column(db.Float, default=0.0)
    discount = db.Column(db.Float, default=0.0)
    items_data = db.Column(db.Text)
    payment_method = db.Column(db.String(50), default='cash')
    notes = db.Column(db.Text)
    status = db.Column(db.String(20), default='pending')
    validated_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    validated_at = db.Column(db.DateTime)
    sale_id = db.Column(db.Integer, db.ForeignKey('sales.id'))
    rejection_reason = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    creator = db.relationship('User', foreign_keys=[created_by], backref='temp_sales_created')
    validator = db.relationship('User', foreign_keys=[validated_by], backref='temp_sales_validated')
    customer = db.relationship('Customer', backref='temp_sales')
    final_sale = db.relationship('Sale', backref='temp_sale', uselist=False)

from datetime import datetime
from app import db
from werkzeug.security import generate_password_hash, check_password_hash

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    phone = db.Column(db.String(20))
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class PurchaseRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    item_name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    quantity = db.Column(db.Integer, nullable=False)
    unit_price = db.Column(db.Float, nullable=False)
    total_amount = db.Column(db.Float, nullable=False)
    supplier = db.Column(db.String(200))
    justification = db.Column(db.Text, nullable=False)
    urgency = db.Column(db.String(50), default='Normal')
    status = db.Column(db.String(50), default='Pending')
    admin_notes = db.Column(db.Text)
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)
    reviewed_at = db.Column(db.DateTime)
    
    user = db.relationship('User', backref=db.backref('purchase_requests', lazy=True))

class ExpenseRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    expense_id = db.Column(db.String(50), unique=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    department = db.Column(db.String(100), nullable=False)
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(50), default='Pending')
    admin_notes = db.Column(db.Text)
    reviewed_at = db.Column(db.DateTime)
    
    user = db.relationship('User', backref=db.backref('expense_records', lazy=True))

class ExpenseItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    expense_record_id = db.Column(db.Integer, db.ForeignKey('expense_record.id'), nullable=False)
    description = db.Column(db.String(500), nullable=False)
    purpose = db.Column(db.String(300), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    rate = db.Column(db.Float, nullable=False)
    amount = db.Column(db.Float, nullable=False)
    voucher_filename = db.Column(db.String(255))
    
    expense_record = db.relationship('ExpenseRecord', backref=db.backref('expense_items', lazy=True, cascade='all, delete-orphan'))

class CashDemand(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    demander_name = db.Column(db.String(200), nullable=False)
    demander_id = db.Column(db.String(100), nullable=False)
    demand_time = db.Column(db.DateTime, default=datetime.utcnow)
    purpose = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    amount = db.Column(db.Float, nullable=False)
    department = db.Column(db.String(100), nullable=False)
    urgency = db.Column(db.String(50), default='Normal')
    payment_method = db.Column(db.String(50), default='Bank Transfer')
    status = db.Column(db.String(50), default='Pending')
    admin_notes = db.Column(db.Text)
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)
    reviewed_at = db.Column(db.DateTime)
    
    user = db.relationship('User', backref=db.backref('cash_demands', lazy=True))

class EmployeeRegistration(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(20))
    department = db.Column(db.String(100), nullable=False)
    position = db.Column(db.String(100), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    salary = db.Column(db.Float)
    employee_id = db.Column(db.String(50))
    id_number = db.Column(db.String(50))
    photo_filename = db.Column(db.String(255))
    id_photo_filename = db.Column(db.String(255))
    other_files = db.Column(db.Text)  # JSON string for multiple files
    status = db.Column(db.String(50), default='Pending')
    admin_notes = db.Column(db.Text)
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)
    reviewed_at = db.Column(db.DateTime)

class AppSettings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    setting_key = db.Column(db.String(100), unique=True, nullable=False)
    setting_value = db.Column(db.Text)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

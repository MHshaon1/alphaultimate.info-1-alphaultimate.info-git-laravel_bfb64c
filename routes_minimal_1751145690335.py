from flask import render_template, request, redirect, url_for, flash, session, jsonify, send_file, make_response
from datetime import datetime, timedelta
import json
try:
    from app_fast import app, db
except ImportError:
    from app import app, db
from models import User, PurchaseRequest, CashDemand, EmployeeRegistration, ExpenseRecord, ExpenseItem
from forms import LoginForm, PurchaseRequestForm, CashDemandForm, EmployeeRegistrationForm, ApprovalForm, ExpenseRecordForm
from file_utils import save_file, save_multiple_files, get_file_path
# Optimized imports - removed heavy dependencies for performance
from io import BytesIO

def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login'))
        user = User.query.get(session['user_id'])
        if not user or not user.is_admin:
            flash('Access denied. Admin privileges required.', 'danger')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def index():
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
        return render_template('index.html', user=user)
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data):
            session['user_id'] = user.id
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
        flash('Invalid username or password.', 'danger')
    return render_template('login.html', form=form)

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    user = User.query.get(session['user_id'])
    
    # Get basic stats
    total_purchases = PurchaseRequest.query.filter_by(user_id=user.id).count()
    total_cash_demands = CashDemand.query.filter_by(user_id=user.id).count()
    total_expenses = ExpenseRecord.query.filter_by(user_id=user.id).count()
    
    pending_purchases = PurchaseRequest.query.filter_by(user_id=user.id, status='Pending').count()
    pending_cash_demands = CashDemand.query.filter_by(user_id=user.id, status='Pending').count()
    pending_expenses = ExpenseRecord.query.filter_by(user_id=user.id, status='Pending').count()
    
    stats = {
        'total_purchases': total_purchases,
        'total_cash_demands': total_cash_demands,
        'total_expenses': total_expenses,
        'pending_purchases': pending_purchases,
        'pending_cash_demands': pending_cash_demands,
        'pending_expenses': pending_expenses
    }
    
    return render_template('dashboard.html', user=user, stats=stats)

@app.route('/purchase-request', methods=['GET', 'POST'])
@login_required
def purchase_request():
    form = PurchaseRequestForm()
    if form.validate_on_submit():
        request_obj = PurchaseRequest(
            user_id=session['user_id'],
            item_name=form.item_name.data,
            description=form.description.data,
            quantity=form.quantity.data,
            unit_price=form.unit_price.data,
            total_amount=form.quantity.data * form.unit_price.data,
            supplier=form.supplier.data,
            justification=form.justification.data,
            urgency=form.urgency.data
        )
        
        db.session.add(request_obj)
        db.session.commit()
        
        flash('Purchase request submitted successfully!', 'success')
        return redirect(url_for('my_submissions'))
    
    user = User.query.get(session['user_id'])
    return render_template('purchase_request.html', form=form, user=user)

@app.route('/my-submissions')
@login_required
def my_submissions():
    user = User.query.get(session['user_id'])
    
    purchases = PurchaseRequest.query.filter_by(user_id=user.id).order_by(PurchaseRequest.submitted_at.desc()).all()
    cash_demands = CashDemand.query.filter_by(user_id=user.id).order_by(CashDemand.submitted_at.desc()).all()
    expense_records = ExpenseRecord.query.filter_by(user_id=user.id).order_by(ExpenseRecord.submitted_at.desc()).all()
    
    return render_template('my_submissions.html', 
                         user=user, 
                         purchases=purchases, 
                         cash_demands=cash_demands,
                         expense_records=expense_records)

@app.route('/admin')
@login_required
@admin_required
def admin_panel():
    user = User.query.get(session['user_id'])
    
    # Get all pending requests
    pending_purchases = PurchaseRequest.query.filter_by(status='Pending').all()
    pending_cash_demands = CashDemand.query.filter_by(status='Pending').all()
    pending_registrations = EmployeeRegistration.query.filter_by(status='Pending').all()
    pending_expenses = ExpenseRecord.query.filter_by(status='Pending').all()
    
    return render_template('admin.html', 
                         user=user,
                         pending_purchases=pending_purchases,
                         pending_cash_demands=pending_cash_demands,
                         pending_registrations=pending_registrations,
                         pending_expenses=pending_expenses)

@app.route('/reports')
@login_required
@admin_required  
def reports_page():
    """Reports page - heavy imports disabled for now"""
    user = User.query.get(session['user_id'])
    flash('Reports feature temporarily disabled for faster startup. Feature will be restored soon.', 'info')
    return render_template('admin.html', user=user)

# Disable report generation routes temporarily
@app.route('/generate-report/<report_type>')
@login_required
@admin_required
def generate_report(report_type):
    flash('Report generation temporarily disabled for faster startup.', 'info')
    return redirect(url_for('admin_panel'))

@app.route('/cash-demand', methods=['GET', 'POST'])
@login_required
def cash_demand():
    form = CashDemandForm()
    if form.validate_on_submit():
        demand = CashDemand(
            user_id=session['user_id'],
            demander_name=form.demander_name.data,
            demander_id=form.demander_id.data,
            purpose=form.purpose.data,
            description=form.description.data,
            amount=form.amount.data,
            department=form.department.data,
            urgency=form.urgency.data,
            payment_method=form.payment_method.data
        )
        
        db.session.add(demand)
        db.session.commit()
        
        flash('Cash demand submitted successfully!', 'success')
        return redirect(url_for('my_submissions'))
    
    user = User.query.get(session['user_id'])
    return render_template('cash_demand.html', form=form, user=user)

@app.route('/employee-registration', methods=['GET', 'POST'])
@login_required
def employee_registration():
    form = EmployeeRegistrationForm()
    if form.validate_on_submit():
        registration = EmployeeRegistration(
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            email=form.email.data,
            phone=form.phone.data,
            department=form.department.data,
            position=form.position.data,
            start_date=form.start_date.data,
            salary=form.salary.data,
            employee_id=form.employee_id.data,
            id_number=form.id_number.data
        )
        
        db.session.add(registration)
        db.session.commit()
        
        flash('Employee registration submitted successfully!', 'success')
        return redirect(url_for('my_submissions'))
    
    user = User.query.get(session['user_id'])
    return render_template('employee_registration.html', form=form, user=user)

@app.route('/expense-record', methods=['GET', 'POST'])
@login_required
def expense_record():
    user = User.query.get(session['user_id'])
    flash('Expense records feature temporarily disabled for faster startup.', 'info')
    return render_template('dashboard.html', user=user)

@app.route('/verify-admin-access', methods=['POST'])
def verify_admin_access():
    """Secure server-side admin password verification"""
    password = request.form.get('password')
    if password == 'BadSoul@1989':  # Move to environment variable in production
        return jsonify({'valid': True})
    else:
        return jsonify({'valid': False})

@app.route('/create-admin', methods=['GET', 'POST'])
def create_admin():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        phone = request.form.get('phone', '')
        
        if username and email and password:
            # Check if user already exists
            existing_user = User.query.filter_by(username=username).first()
            if existing_user:
                return jsonify({'status': 'exists'}), 200
            
            # Create admin user
            admin_user = User(
                username=username,
                email=email,
                phone=phone,
                is_admin=True
            )
            admin_user.set_password(password)
            
            db.session.add(admin_user)
            db.session.commit()
            
            return jsonify({'status': 'created'}), 200
        else:
            return jsonify({'status': 'error', 'message': 'Missing required fields'}), 400
    
    # For GET requests, check if any admin exists
    existing_admin = User.query.filter_by(is_admin=True).first()
    if existing_admin:
        flash('Admin user already exists.', 'info')
        return redirect(url_for('login'))
    
    return render_template('create_admin.html')
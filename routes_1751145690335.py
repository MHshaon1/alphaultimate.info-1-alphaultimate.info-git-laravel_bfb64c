from flask import render_template, request, redirect, url_for, flash, session, jsonify, send_file, make_response
from datetime import datetime, timedelta
import json
from app import app, db
from models import User, PurchaseRequest, CashDemand, EmployeeRegistration, ExpenseRecord, ExpenseItem
from forms import LoginForm, PurchaseRequestForm, CashDemandForm, EmployeeRegistrationForm, ApprovalForm, ExpenseRecordForm
# Import report generator normally since lazy loading isn't working
from report_generator import ReportGenerator, create_reports_directory
from file_utils import save_file, save_multiple_files, get_file_path
from sms_service import sms_service
from ai_assistant import ai_assistant
from api_key_manager import api_key_manager
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
            flash(f'Welcome back, {user.username}!', 'success')
            return redirect(url_for('index'))
        flash('Invalid username or password.', 'danger')
    return render_template('index.html', form=form, show_login=True)

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))

@app.route('/purchase-request', methods=['GET', 'POST'])
@login_required
def purchase_request():
    form = PurchaseRequestForm()
    if form.validate_on_submit():
        # Calculate total amount
        total_amount = (form.quantity.data or 0) * (form.unit_price.data or 0)
        
        # AI urgency analysis
        ai_analysis = 
try:
    urgency_result = ai_assistant.analyze_request_urgency(
            form.description.data or "",
            form.justification.data or ""
        )
    urgency = urgency_result.get("urgency", "Normal")
    confidence = urgency_result.get("confidence", 0.5)
    reasoning = urgency_result.get("reasoning", "AI reasoning unavailable.")
except Exception as e:
    app.logger.error("AI urgency analysis failed", exc_info=e)
    urgency = "Normal"
    confidence = 0.0
    reasoning = "Fallback: AI failed to process."

        
        # Use AI suggested urgency if available, otherwise use form selection
        urgency = ai_analysis.get('urgency', form.urgency.data)
        
        purchase = PurchaseRequest(
            user_id=session['user_id'],
            item_name=form.item_name.data,
            description=form.description.data,
            quantity=form.quantity.data,
            unit_price=form.unit_price.data,
            total_amount=total_amount,
            supplier=form.supplier.data,
            justification=form.justification.data,
            urgency=urgency
        )
        
        db.session.add(purchase)
        db.session.commit()
        
        # Send SMS notification to admins
        admins = User.query.filter_by(is_admin=True).all()
        user = User.query.get(session['user_id'])
        
        for admin in admins:
            if admin.phone:
                sms_service.send_admin_alert(
                    admin.phone,
                    "purchase request",
                    user.username if user else "Unknown User"
                )
        
        # Show AI analysis in flash message if available
        if ai_analysis.get('reasoning'):
            flash(f'Purchase request submitted! AI Analysis: {ai_analysis["reasoning"]}', 'success')
        else:
            flash('Purchase request submitted successfully!', 'success')
            
        return redirect(url_for('my_submissions'))
    return render_template('purchase_form.html', form=form)

@app.route('/cash-demand', methods=['GET', 'POST'])
@login_required
def cash_demand():
    form = CashDemandForm()
    user = User.query.get(session['user_id'])
    
    # Pre-populate demander name and ID
    if request.method == 'GET':
        form.demander_name.data = f"{user.username}"
        form.demander_id.data = str(user.id)
    
    if form.validate_on_submit():
        demand = CashDemand(
            user_id=session['user_id'],
            demander_name=form.demander_name.data,
            demander_id=form.demander_id.data,
            demand_time=datetime.utcnow(),
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
    return render_template('cash_demand_form.html', form=form, user=user)

@app.route('/employee-registration', methods=['GET', 'POST'])
def employee_registration():
    form = EmployeeRegistrationForm()
    if form.validate_on_submit():
        # Handle file uploads
        photo_filename = None
        id_photo_filename = None
        other_files_list = []
        
        if form.photo.data:
            photo_filename = save_file(form.photo.data, 'photos', 'images')
        
        if form.id_photo.data:
            id_photo_filename = save_file(form.id_photo.data, 'id_photos', 'images')
        
        if form.other_files.data:
            other_files_list = save_multiple_files(form.other_files.data, 'documents', 'documents')
        
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
            id_number=form.id_number.data,
            photo_filename=photo_filename,
            id_photo_filename=id_photo_filename,
            other_files=json.dumps(other_files_list) if other_files_list else None
        )
        db.session.add(registration)
        db.session.commit()
        flash('Employee registration submitted successfully!', 'success')
        return redirect(url_for('index'))
    return render_template('employee_registration.html', form=form)

@app.route('/my-submissions')
@login_required
def my_submissions():
    user_id = session['user_id']
    purchases = PurchaseRequest.query.filter_by(user_id=user_id).order_by(PurchaseRequest.submitted_at.desc()).all()
    demands = CashDemand.query.filter_by(user_id=user_id).order_by(CashDemand.submitted_at.desc()).all()
    expenses = ExpenseRecord.query.filter_by(user_id=user_id).order_by(ExpenseRecord.submitted_at.desc()).all()
    return render_template('my_submissions.html', purchases=purchases, demands=demands, expenses=expenses)

@app.route('/admin')
@admin_required
def admin_panel():
    purchases = PurchaseRequest.query.order_by(PurchaseRequest.submitted_at.desc()).all()
    demands = CashDemand.query.order_by(CashDemand.submitted_at.desc()).all()
    registrations = EmployeeRegistration.query.order_by(EmployeeRegistration.submitted_at.desc()).all()
    expenses = ExpenseRecord.query.order_by(ExpenseRecord.submitted_at.desc()).all()
    
    # Get service status and setup messages
    service_status = api_key_manager.check_services_status()
    setup_messages = api_key_manager.generate_setup_message()
    
    # Generate AI insights for expense patterns
    expense_data = []
    for expense in expenses[:10]:  # Analyze last 10 expenses
        expense_data.append({
            'department': expense.department,
            'amount': sum(item.amount for item in expense.expense_items),
            'date': expense.submitted_at.strftime('%Y-%m-%d'),
            'status': expense.status
        })
    
    ai_insights = 
try:
    expense_analysis = ai_assistant.analyze_expense_patterns(expense_data)
except Exception as e:
    app.logger.error("Expense pattern AI analysis failed", exc_info=e)
    expense_analysis = {"summary": "No analysis available", "patterns": []}
 if expense_data else None
    
    return render_template('admin_panel.html', 
                         purchases=purchases, 
                         demands=demands, 
                         registrations=registrations, 
                         expenses=expenses,
                         service_status=service_status,
                         setup_messages=setup_messages,
                         ai_insights=ai_insights)

@app.route('/admin/approve/<string:type>/<int:id>', methods=['POST'])
@admin_required
def approve_request(type, id):
    form = ApprovalForm()
    if form.validate_on_submit():
        if type == 'purchase':
            item = PurchaseRequest.query.get_or_404(id)
        elif type == 'demand':
            item = CashDemand.query.get_or_404(id)
        elif type == 'registration':
            item = EmployeeRegistration.query.get_or_404(id)
        elif type == 'expense':
            item = ExpenseRecord.query.get_or_404(id)
        else:
            flash('Invalid request type.', 'danger')
            return redirect(url_for('admin_panel'))
        
        # Generate AI approval notes if admin notes are empty
        if not form.admin_notes.data and hasattr(item, 'item_name'):
            ai_notes = 
try:
    ai_notes_result = ai_assistant.generate_approval_notes(
                type, 
                getattr(item, 'item_name', 'N/A')
    approval_notes = ai_notes_result.get("notes", "No AI notes available")
except Exception as e:
    app.logger.error("AI approval notes generation failed", exc_info=e)
    approval_notes = "AI notes unavailable."
,
                getattr(item, 'total_amount', getattr(item, 'amount', 0)),
                getattr(item, 'department', 'N/A')
            )
            item.admin_notes = ai_notes
        else:
            item.admin_notes = form.admin_notes.data
        
        item.status = form.status.data
        item.reviewed_at = datetime.utcnow()
        db.session.commit()
        
        # Send SMS notification to the user who submitted the request
        user = User.query.get(item.user_id)
        if user and user.phone:
            sms_service.send_approval_notification(
                user.phone,
                type,
                form.status.data
            )
        
        flash(f'Request {form.status.data.lower()} successfully!', 'success')
    return redirect(url_for('admin_panel'))

@app.route('/dashboard')
@login_required
def dashboard():
    user = User.query.get(session['user_id'])
    if user.is_admin:
        # Admin dashboard with all data
        total_purchases = PurchaseRequest.query.count()
        total_demands = CashDemand.query.count()
        total_registrations = EmployeeRegistration.query.count()
        
        pending_purchases = PurchaseRequest.query.filter_by(status='Pending').count()
        pending_demands = CashDemand.query.filter_by(status='Pending').count()
        pending_registrations = EmployeeRegistration.query.filter_by(status='Pending').count()
        
        total_purchase_amount = db.session.query(db.func.sum(PurchaseRequest.total_amount)).filter_by(status='Approved').scalar() or 0
        total_demand_amount = db.session.query(db.func.sum(CashDemand.amount)).filter_by(status='Approved').scalar() or 0
        
        stats = {
            'total_purchases': total_purchases,
            'total_demands': total_demands,
            'total_registrations': total_registrations,
            'pending_purchases': pending_purchases,
            'pending_demands': pending_demands,
            'pending_registrations': pending_registrations,
            'total_purchase_amount': total_purchase_amount,
            'total_demand_amount': total_demand_amount
        }
    else:
        # User dashboard with their data only
        user_id = session['user_id']
        total_purchases = PurchaseRequest.query.filter_by(user_id=user_id).count()
        total_demands = CashDemand.query.filter_by(user_id=user_id).count()
        
        pending_purchases = PurchaseRequest.query.filter_by(user_id=user_id, status='Pending').count()
        pending_demands = CashDemand.query.filter_by(user_id=user_id, status='Pending').count()
        
        total_purchase_amount = db.session.query(db.func.sum(PurchaseRequest.total_amount)).filter_by(user_id=user_id, status='Approved').scalar() or 0
        total_demand_amount = db.session.query(db.func.sum(CashDemand.amount)).filter_by(user_id=user_id, status='Approved').scalar() or 0
        
        stats = {
            'total_purchases': total_purchases,
            'total_demands': total_demands,
            'total_registrations': 0,
            'pending_purchases': pending_purchases,
            'pending_demands': pending_demands,
            'pending_registrations': 0,
            'total_purchase_amount': total_purchase_amount,
            'total_demand_amount': total_demand_amount
        }
    
    return render_template('dashboard.html', stats=stats, user=user)

@app.route('/api/dashboard-data')
@login_required
def dashboard_data():
    user = User.query.get(session['user_id'])
    
    if user.is_admin:
        # Admin gets all data
        purchases = PurchaseRequest.query.all()
        demands = CashDemand.query.all()
    else:
        # Users get only their data
        user_id = session['user_id']
        purchases = PurchaseRequest.query.filter_by(user_id=user_id).all()
        demands = CashDemand.query.filter_by(user_id=user_id).all()
    
    # Status distribution
    purchase_status = {'Pending': 0, 'Approved': 0, 'Rejected': 0}
    demand_status = {'Pending': 0, 'Approved': 0, 'Rejected': 0}
    
    for p in purchases:
        purchase_status[p.status] = purchase_status.get(p.status, 0) + 1
    
    for d in demands:
        demand_status[d.status] = demand_status.get(d.status, 0) + 1
    
    # Monthly data for the last 6 months
    monthly_data = {}
    for p in purchases:
        month_key = p.submitted_at.strftime('%Y-%m')
        if month_key not in monthly_data:
            monthly_data[month_key] = {'purchases': 0, 'demands': 0, 'purchase_amount': 0, 'demand_amount': 0}
        monthly_data[month_key]['purchases'] += 1
        if p.status == 'Approved':
            monthly_data[month_key]['purchase_amount'] += p.total_amount
    
    for d in demands:
        month_key = d.submitted_at.strftime('%Y-%m')
        if month_key not in monthly_data:
            monthly_data[month_key] = {'purchases': 0, 'demands': 0, 'purchase_amount': 0, 'demand_amount': 0}
        monthly_data[month_key]['demands'] += 1
        if d.status == 'Approved':
            monthly_data[month_key]['demand_amount'] += d.amount
    
    return jsonify({
        'purchase_status': purchase_status,
        'demand_status': demand_status,
        'monthly_data': monthly_data
    })

@app.route('/reports')
@login_required
def reports_page():
    """Reports page for generating PDF reports"""
    user = User.query.get(session['user_id'])
    
    # Get current date info for form defaults
    now = datetime.now()
    today = now.date()
    monday = today - timedelta(days=today.weekday())
    
    return render_template('reports.html', 
                         user=user,
                         today=today.strftime('%Y-%m-%d'),
                         monday=monday.strftime('%Y-%m-%d'),
                         current_month=now.month,
                         current_year=now.year)

@app.route('/generate-report/<report_type>')
@login_required
def generate_report(report_type):
    """Generate and download PDF report"""
    user = User.query.get(session['user_id'])
    if not user.is_admin:
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('dashboard'))
    
    generator = ReportGenerator()
    
    try:
        if report_type == 'daily':
            date_str = request.args.get('date')
            if date_str:
                report_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            else:
                report_date = datetime.now().date()
            pdf_data, filename = generator.generate_daily_report(report_date)
            
        elif report_type == 'weekly':
            week_str = request.args.get('week')
            if week_str:
                week_start = datetime.strptime(week_str, '%Y-%m-%d').date()
            else:
                today = datetime.now().date()
                week_start = today - timedelta(days=today.weekday())
            pdf_data, filename = generator.generate_weekly_report(week_start)
            
        elif report_type == 'monthly':
            year = int(request.args.get('year', datetime.now().year))
            month = int(request.args.get('month', datetime.now().month))
            pdf_data, filename = generator.generate_monthly_report(year, month)
            
        else:
            flash('Invalid report type.', 'danger')
            return redirect(url_for('reports_page'))
        
        # Create response
        response = make_response(pdf_data)
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'attachment; filename={filename}'
        
        return response
        
    except Exception as e:
        flash(f'Error generating report: {str(e)}', 'danger')
        return redirect(url_for('reports_page'))

@app.route('/preview-report/<report_type>')
@login_required 
def preview_report(report_type):
    """Preview PDF report in browser"""
    user = User.query.get(session['user_id'])
    if not user.is_admin:
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('dashboard'))
    
    generator = ReportGenerator()
    
    try:
        if report_type == 'daily':
            date_str = request.args.get('date')
            if date_str:
                report_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            else:
                report_date = datetime.now().date()
            pdf_data, filename = generator.generate_daily_report(report_date)
            
        elif report_type == 'weekly':
            week_str = request.args.get('week')
            if week_str:
                week_start = datetime.strptime(week_str, '%Y-%m-%d').date()
            else:
                today = datetime.now().date()
                week_start = today - timedelta(days=today.weekday())
            pdf_data, filename = generator.generate_weekly_report(week_start)
            
        elif report_type == 'monthly':
            year = int(request.args.get('year', datetime.now().year))
            month = int(request.args.get('month', datetime.now().month))
            pdf_data, filename = generator.generate_monthly_report(year, month)
            
        else:
            flash('Invalid report type.', 'danger')
            return redirect(url_for('reports_page'))
        
        # Create response for inline viewing
        response = make_response(pdf_data)
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'inline; filename={filename}'
        
        return response
        
    except Exception as e:
        flash(f'Error generating report: {str(e)}', 'danger')
        return redirect(url_for('reports_page'))

@app.route('/expense-record', methods=['GET', 'POST'])
@login_required
def expense_record():
    form = ExpenseRecordForm()
    user = User.query.get(session['user_id'])
    
    if request.method == 'POST':
        # Generate unique expense ID if not provided
        expense_id = request.form.get('expense_id')
        if not expense_id:
            expense_id = f"EXP{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        # Create expense record
        expense = ExpenseRecord(
            expense_id=expense_id,
            user_id=session['user_id'],
            department=request.form.get('department')
        )
        db.session.add(expense)
        db.session.flush()  # Get the ID
        
        # Process expense items
        item_count = 0
        for i in range(10):  # Max 10 items
            description = request.form.get(f'items[{i}][description]')
            if description:  # Only process if description exists
                purpose = request.form.get(f'items[{i}][purpose]')
                quantity = request.form.get(f'items[{i}][quantity]', type=int)
                rate = request.form.get(f'items[{i}][rate]', type=float)
                amount = request.form.get(f'items[{i}][amount]', type=float)
                
                # Handle voucher upload
                voucher_filename = None
                voucher_file = request.files.get(f'items[{i}][voucher]')
                if voucher_file and voucher_file.filename:
                    voucher_filename = save_file(voucher_file, 'vouchers', 'vouchers')
                
                expense_item = ExpenseItem(
                    expense_record_id=expense.id,
                    description=description,
                    purpose=purpose,
                    quantity=quantity,
                    rate=rate,
                    amount=amount,
                    voucher_filename=voucher_filename
                )
                db.session.add(expense_item)
                item_count += 1
        
        if item_count > 0:
            db.session.commit()
            flash(f'Expense record submitted successfully with {item_count} items!', 'success')
            return redirect(url_for('my_submissions'))
        else:
            db.session.rollback()
            flash('Please add at least one expense item.', 'warning')
    
    return render_template('expense_record_form.html', form=form, user=user)

@app.route('/admin/settings')
@admin_required
def admin_settings():
    """Admin settings page for API key management"""
    service_status = api_key_manager.check_services_status()
    setup_messages = api_key_manager.generate_setup_message()
    missing_keys = api_key_manager.get_missing_keys()
    
    return render_template('admin_settings.html', 
                         service_status=service_status,
                         setup_messages=setup_messages,
                         missing_keys=missing_keys)

@app.route('/uploads/<subfolder>/<filename>')
def uploaded_file(subfolder, filename):
    """Serve uploaded files"""
    return send_file(get_file_path(filename, subfolder))

# Create default admin user
def create_admin():
    admin = User.query.filter_by(username='admin').first()
    if not admin:
        admin = User(username='admin', email='admin@workdesk.com', is_admin=True)
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()
        print("Default admin user created: admin/admin123")

# Initialize admin on app startup
try:
    with app.app_context():
        create_admin()
except Exception as e:
    print(f"Error creating admin user: {e}")

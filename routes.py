import os
import json
from datetime import datetime, timedelta
from functools import wraps
from flask import render_template, request, redirect, url_for, session, flash, jsonify, send_file
from werkzeug.utils import secure_filename
from app import app, db
from models import User, PurchaseRequest, CashDemand, ExpenseRecord, ExpenseItem, EmployeeRegistration, AppSettings
from forms import LoginForm, PurchaseRequestForm, CashDemandForm, ExpenseRecordForm, EmployeeRegistrationForm, ApprovalForm
from file_utils import save_file, save_multiple_files, init_upload_folders, get_file_path
from ai_assistant import AIAssistant
from sms_service import SMSService
from api_key_manager import APIKeyManager
from report_generator import ReportGenerator, create_reports_directory

# Initialize upload folders and reports directory
init_upload_folders()
create_reports_directory()

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('You need to log in first.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('You need to log in first.', 'warning')
            return redirect(url_for('login'))
        
        user = User.query.get(session['user_id'])
        if not user or not user.is_admin:
            flash('Admin access required.', 'error')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data):
            session['user_id'] = user.id
            session['username'] = user.username
            session['is_admin'] = user.is_admin
            flash(f'Welcome back, {user.username}!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password.', 'error')
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
    
    if user.is_admin:
        # Admin dashboard
        total_purchases = PurchaseRequest.query.count()
        total_demands = CashDemand.query.count()
        total_registrations = EmployeeRegistration.query.count()
        total_expenses = ExpenseRecord.query.count()
        
        pending_purchases = PurchaseRequest.query.filter_by(status='Pending').count()
        pending_demands = CashDemand.query.filter_by(status='Pending').count()
        pending_registrations = EmployeeRegistration.query.filter_by(status='Pending').count()
        pending_expenses = ExpenseRecord.query.filter_by(status='Pending').count()
        
        # Calculate total amounts
        total_purchase_amount = db.session.query(db.func.sum(PurchaseRequest.total_amount)).filter_by(status='Approved').scalar() or 0
        total_demand_amount = db.session.query(db.func.sum(CashDemand.amount)).filter_by(status='Approved').scalar() or 0
        
        stats = {
            'total_purchases': total_purchases,
            'total_demands': total_demands,
            'total_registrations': total_registrations,
            'total_expenses': total_expenses,
            'pending_purchases': pending_purchases,
            'pending_demands': pending_demands,
            'pending_registrations': pending_registrations,
            'pending_expenses': pending_expenses,
            'total_purchase_amount': total_purchase_amount,
            'total_demand_amount': total_demand_amount
        }
        
        # Get recent activity
        recent_purchases = PurchaseRequest.query.order_by(PurchaseRequest.submitted_at.desc()).limit(5).all()
        recent_demands = CashDemand.query.order_by(CashDemand.submitted_at.desc()).limit(5).all()
        recent_registrations = EmployeeRegistration.query.order_by(EmployeeRegistration.submitted_at.desc()).limit(5).all()
        recent_expenses = ExpenseRecord.query.order_by(ExpenseRecord.submitted_at.desc()).limit(5).all()
        
        return render_template('admin_dashboard.html', stats=stats, 
                             recent_purchases=recent_purchases,
                             recent_demands=recent_demands,
                             recent_registrations=recent_registrations,
                             recent_expenses=recent_expenses)
    else:
        # User dashboard
        user_purchases = PurchaseRequest.query.filter_by(user_id=user.id).order_by(PurchaseRequest.submitted_at.desc()).limit(10).all()
        user_demands = CashDemand.query.filter_by(user_id=user.id).order_by(CashDemand.submitted_at.desc()).limit(10).all()
        user_expenses = ExpenseRecord.query.filter_by(user_id=user.id).order_by(ExpenseRecord.submitted_at.desc()).limit(10).all()
        
        return render_template('dashboard.html', 
                             user_purchases=user_purchases,
                             user_demands=user_demands,
                             user_expenses=user_expenses)

@app.route('/purchase_request', methods=['GET', 'POST'])
@login_required
def purchase_request():
    form = PurchaseRequestForm()
    if form.validate_on_submit():
        # Calculate total amount
        total_amount = form.quantity.data * form.unit_price.data
        
        # Create new purchase request
        purchase = PurchaseRequest()
        purchase.user_id = session['user_id']
        purchase.item_name = form.item_name.data
        purchase.description = form.description.data
        purchase.quantity = form.quantity.data
        purchase.unit_price = form.unit_price.data
        purchase.total_amount = total_amount
        purchase.supplier = form.supplier.data
        purchase.justification = form.justification.data
        purchase.urgency = form.urgency.data
        
        # AI Analysis for urgency if available
        try:
            ai_assistant = AIAssistant()
            ai_analysis = ai_assistant.analyze_request_urgency(form.description.data, form.justification.data)
            if ai_analysis and 'urgency' in ai_analysis:
                purchase.urgency = ai_analysis['urgency']
        except Exception:
            pass  # Graceful fallback if AI service unavailable
        
        db.session.add(purchase)
        db.session.commit()
        
        # Send SMS notification to admin if configured
        try:
            sms_service = SMSService()
            sms_service.send_admin_alert(None, 'Purchase Request', session['username'])
        except Exception:
            pass  # Graceful fallback if SMS service unavailable
        
        flash('Purchase request submitted successfully!', 'success')
        return redirect(url_for('dashboard'))
    
    return render_template('purchase_request.html', form=form)

@app.route('/cash_demand', methods=['GET', 'POST'])
@login_required
def cash_demand():
    form = CashDemandForm()
    if form.validate_on_submit():
        # Create new cash demand
        demand = CashDemand()
        demand.user_id = session['user_id']
        demand.demander_name = form.demander_name.data
        demand.demander_id = form.demander_id.data
        demand.purpose = form.purpose.data
        demand.description = form.description.data
        demand.amount = form.amount.data
        demand.department = form.department.data
        demand.urgency = form.urgency.data
        demand.payment_method = form.payment_method.data
        
        db.session.add(demand)
        db.session.commit()
        
        # Send SMS notification to admin if configured
        try:
            sms_service = SMSService()
            sms_service.send_admin_alert(None, 'Cash Demand', session['username'])
        except Exception:
            pass  # Graceful fallback if SMS service unavailable
        
        flash('Cash demand submitted successfully!', 'success')
        return redirect(url_for('dashboard'))
    
    return render_template('cash_demand.html', form=form)

@app.route('/expense_record', methods=['GET', 'POST'])
@login_required
def expense_record():
    form = ExpenseRecordForm()
    if form.validate_on_submit():
        # Create new expense record
        expense = ExpenseRecord()
        expense.expense_id = form.expense_id.data
        expense.user_id = session['user_id']
        expense.department = form.department.data
        
        db.session.add(expense)
        db.session.flush()  # Get the ID
        
        # Process expense items
        for i in range(1, 11):  # Support up to 10 items
            description = request.form.get(f'item_{i}_description')
            if description:
                item = ExpenseItem()
                item.expense_record_id = expense.id
                item.description = description
                item.purpose = request.form.get(f'item_{i}_purpose', '')
                item.quantity = int(request.form.get(f'item_{i}_quantity', 1))
                item.rate = float(request.form.get(f'item_{i}_rate', 0))
                item.amount = item.quantity * item.rate
                
                # Handle voucher upload
                voucher_file = request.files.get(f'item_{i}_voucher')
                if voucher_file and voucher_file.filename:
                    voucher_filename = save_file(voucher_file, expense.expense_id, 'vouchers')
                    item.voucher_filename = voucher_filename
                
                db.session.add(item)
        
        db.session.commit()
        flash('Expense record submitted successfully!', 'success')
        return redirect(url_for('dashboard'))
    
    return render_template('expense_record.html', form=form)

@app.route('/employee_registration', methods=['GET', 'POST'])
@login_required
def employee_registration():
    form = EmployeeRegistrationForm()
    if form.validate_on_submit():
        # Create new employee registration
        registration = EmployeeRegistration()
        registration.first_name = form.first_name.data
        registration.last_name = form.last_name.data
        registration.email = form.email.data
        registration.phone = form.phone.data
        registration.department = form.department.data
        registration.position = form.position.data
        registration.start_date = form.start_date.data
        registration.salary = form.salary.data
        registration.employee_id = form.employee_id.data
        registration.id_number = form.id_number.data
        
        # Handle file uploads
        employee_folder = f"{registration.first_name}_{registration.last_name}_{datetime.now().strftime('%Y%m%d')}"
        
        if form.photo.data:
            photo_filename = save_file(form.photo.data, employee_folder, 'images')
            registration.photo_filename = photo_filename
        
        if form.id_photo.data:
            id_photo_filename = save_file(form.id_photo.data, employee_folder, 'images')
            registration.id_photo_filename = id_photo_filename
        
        if form.other_files.data:
            other_filenames = save_multiple_files(form.other_files.data, employee_folder, 'documents')
            registration.other_files = json.dumps(other_filenames)
        
        db.session.add(registration)
        db.session.commit()
        flash('Employee registration submitted successfully!', 'success')
        return redirect(url_for('dashboard'))
    
    return render_template('employee_registration.html', form=form)

@app.route('/my_submissions')
@login_required
def my_submissions():
    user_id = session['user_id']
    purchases = PurchaseRequest.query.filter_by(user_id=user_id).order_by(PurchaseRequest.submitted_at.desc()).all()
    demands = CashDemand.query.filter_by(user_id=user_id).order_by(CashDemand.submitted_at.desc()).all()
    expenses = ExpenseRecord.query.filter_by(user_id=user_id).order_by(ExpenseRecord.submitted_at.desc()).all()
    
    return render_template('my_submissions.html', 
                         purchases=purchases, 
                         demands=demands, 
                         expenses=expenses)

@app.route('/admin_panel')
@admin_required
def admin_panel():
    # Get all pending requests
    purchases = PurchaseRequest.query.filter_by(status='Pending').order_by(PurchaseRequest.submitted_at.desc()).all()
    demands = CashDemand.query.filter_by(status='Pending').order_by(CashDemand.submitted_at.desc()).all()
    registrations = EmployeeRegistration.query.filter_by(status='Pending').order_by(EmployeeRegistration.submitted_at.desc()).all()
    expenses = ExpenseRecord.query.filter_by(status='Pending').order_by(ExpenseRecord.submitted_at.desc()).all()
    
    # Get service status
    service_status = APIKeyManager.check_services_status()
    setup_messages = APIKeyManager.generate_setup_message()
    
    # Get AI insights if available
    ai_insights = None
    try:
        ai_assistant = AIAssistant()
        expense_data = []
        for expense in expenses:
            expense_items = ExpenseItem.query.filter_by(expense_record_id=expense.id).all()
            total_amount = sum(item.amount for item in expense_items)
            expense_data.append({
                'department': expense.department,
                'amount': total_amount,
                'date': expense.submitted_at
            })
        
        if expense_data:
            ai_insights = ai_assistant.analyze_expense_patterns(expense_data)
    except Exception:
        pass  # Graceful fallback if AI service unavailable
    
    form = ApprovalForm()  # Create form instance for CSRF token
    
    return render_template('admin_panel.html', 
                         purchases=purchases,
                         demands=demands,
                         registrations=registrations,
                         expenses=expenses,
                         service_status=service_status,
                         setup_messages=setup_messages,
                         ai_insights=ai_insights,
                         form=form)

@app.route('/approve/<type>/<int:id>', methods=['POST'])
@admin_required
def approve_request(type, id):
    form = ApprovalForm()
    if form.validate_on_submit():
        item = None
        if type == 'purchase':
            item = PurchaseRequest.query.get_or_404(id)
            # Generate AI approval notes if available
            try:
                ai_assistant = AIAssistant()
                ai_notes = ai_assistant.generate_approval_notes('purchase', item.item_name, item.total_amount, 'General')
                if ai_notes and not form.admin_notes.data:
                    # Extract string from dict if needed
                    if isinstance(ai_notes, dict):
                        form.admin_notes.data = ai_notes.get('notes', str(ai_notes))
                    else:
                        form.admin_notes.data = str(ai_notes)
            except Exception:
                pass  # Graceful fallback if AI service unavailable
        elif type == 'demand':
            item = CashDemand.query.get_or_404(id)
        elif type == 'registration':
            item = EmployeeRegistration.query.get_or_404(id)
        elif type == 'expense':
            item = ExpenseRecord.query.get_or_404(id)
        
        if item:
            item.status = form.status.data
            # Ensure admin_notes is always a string
            admin_notes = form.admin_notes.data
            if isinstance(admin_notes, dict):
                item.admin_notes = admin_notes.get('notes', '') or admin_notes.get('message', '') or str(admin_notes)
            else:
                item.admin_notes = str(admin_notes) if admin_notes else ''
            item.reviewed_at = datetime.utcnow()
            db.session.commit()
            
            # Send SMS notification to user if configured
            try:
                sms_service = SMSService()
                user = User.query.get(item.user_id if hasattr(item, 'user_id') else None)
                if user and user.phone:
                    sms_service.send_approval_notification(user.phone, type.title(), form.status.data)
            except Exception:
                pass  # Graceful fallback if SMS service unavailable
            
            flash(f'{type.title()} request {form.status.data.lower()} successfully!', 'success')
    
    return redirect(url_for('admin_panel'))

@app.route('/ai_dashboard')
@admin_required
def ai_dashboard():
    """AI-powered dashboard with voice commands and predictions"""
    user = User.query.get(session.get('user_id'))
    return render_template('ai_dashboard.html', user=user)

@app.route('/api/ai-query', methods=['POST'])
@admin_required
def ai_query():
    """Process AI queries for the dashboard"""
    data = request.get_json()
    query = data.get('query', '')
    
    # Initialize AI Assistant
    ai_assistant = AIAssistant()
    
    # Process the query
    response = "I'm analyzing your request about: " + query
    
    # Add specific responses based on query content
    if 'revenue' in query.lower():
        response = "Revenue analysis shows a 12.5% increase trend. Current monthly revenue is $102,000 with projections reaching $125,450 next month."
    elif 'efficiency' in query.lower():
        response = "Department efficiency metrics: IT leads at 92%, followed by Sales at 90% and Finance at 88%. Overall efficiency has improved by 15% this quarter."
    elif 'risk' in query.lower():
        response = "Risk assessment indicates low overall business risk. One area of concern: IT department spending increased by 40%. Recommend budget review."
    
    return jsonify({'response': response})

@app.route('/admin_reports')
@admin_required
def admin_reports():
    return render_template('admin_reports.html')

@app.route('/generate_report', methods=['POST'])
@admin_required
def generate_report():
    report_type = request.form.get('report_type')
    date_input = request.form.get('date')
    
    try:
        generator = ReportGenerator()
        
        if report_type == 'daily':
            date = datetime.strptime(date_input, '%Y-%m-%d').date() if date_input else None
            report_path = generator.generate_daily_report(date)
        elif report_type == 'weekly':
            week_start = datetime.strptime(date_input, '%Y-%m-%d').date() if date_input else None
            report_path = generator.generate_weekly_report(week_start)
        elif report_type == 'monthly':
            if date_input:
                date = datetime.strptime(date_input, '%Y-%m-%d').date()
                report_path = generator.generate_monthly_report(date.year, date.month)
            else:
                report_path = generator.generate_monthly_report()
        else:
            flash('Invalid report type selected.', 'error')
            return redirect(url_for('admin_reports'))
        
        if report_path and os.path.exists(report_path):
            return send_file(report_path, as_attachment=True)
        else:
            flash('Error generating report.', 'error')
    except Exception as e:
        flash(f'Error generating report: {str(e)}', 'error')
    
    return redirect(url_for('admin_reports'))

@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500

# === Leaderboard Routes ===

from flask import render_template, jsonify
from models import LeaderboardEntry, TeamLeaderboard
from app import app, db

@app.route('/leaderboard')
def leaderboard_page():
    return render_template('leaderboard.html')

@app.route('/api/leaderboard')
def get_leaderboard_data():
    # Fetch top individual performers
    top_users = LeaderboardEntry.query.order_by(LeaderboardEntry.xp.desc()).limit(10).all()
    top_teams = TeamLeaderboard.query.order_by(TeamLeaderboard.total_xp.desc()).limit(5).all()

    user_data = [{
        "username": u.username,
        "xp": u.xp,
        "level": u.level,
        "badges": u.badges,
        "streak": u.streak
    } for u in top_users]

    team_data = [{
        "team_name": t.team_name,
        "total_xp": t.total_xp,
        "average_level": t.average_level,
        "member_count": t.member_count
    } for t in top_teams]

    return jsonify({
        "users": user_data,
        "teams": team_data
    })


# === Health Score Route ===

@app.route('/health')
def health_score():
    return render_template('health_score.html')


# === Excel Export Route ===

from report_generator import generate_excel_report

@app.route('/export/excel')
def export_excel():
    return generate_excel_report()


# === Notification Center Route ===

@app.route('/notifications')
def notifications():
    return render_template('notification_center.html')


# === Accounting Dashboard Routes ===

from accounting import get_accounting_summary

@app.route('/accounting')
def accounting_dashboard():
    return render_template('accounting_dashboard.html')

@app.route('/api/accounting')
def api_accounting_data():
    return get_accounting_summary()


# === Mobile + Timesheet Routes ===

from flask import request, redirect, flash
from forms import TimesheetForm
from models import db  # Assumes db is initialized globally
from flask import render_template

@app.route('/mobile')
def mobile_dashboard():
    return render_template('mobile_dashboard.html')

@app.route('/mobile/timesheet', methods=['GET'])
def mobile_timesheet():
    form = TimesheetForm()
    return render_template('timesheet_form.html', form=form)

@app.route('/submit/timesheet', methods=['POST'])
def submit_timesheet():
    form = TimesheetForm()
    if form.validate_on_submit():
        # Create timesheet entry with GPS data
        from models import TimesheetEntry  # Placeholder class name
        entry = TimesheetEntry(
            project=form.project.data,
            hours=form.hours.data,
            latitude=form.latitude.data,
            longitude=form.longitude.data
        )
        db.session.add(entry)
        db.session.commit()
        flash("Timesheet submitted successfully!", "success")
        return redirect('/mobile')
    else:
        flash("Error submitting timesheet. Please check your inputs.", "danger")
        return render_template('timesheet_form.html', form=form)


# === Gantt Chart Route ===

@app.route('/gantt')
def gantt_builder():
    return render_template('gantt_builder.html')


# === AI Assistant Chat Route ===

import json
from flask import request, jsonify
from ai_assistant import RiskPredictor

@app.route('/api/ai-chat', methods=['POST'])
def ai_chat():
    data = request.get_json()
    query = data.get("query", "").lower()

    predictor = RiskPredictor()
    response = "I'm not sure how to help with that."

    if "risk" in query:
        project_data = {}  # In production, fetch actual project context
        risks = predictor.predict_risk(project_data)
        top_risks = sorted(risks.items(), key=lambda r: -r[1]['likelihood'])[:2]
        response = "Top risks detected:
" + "\n".join([f"{k}: {v['impact']} ({v['likelihood']*100:.0f}%)" for k,v in top_risks])
    elif "hello" in query or "hi" in query:
        response = "Hello! I’m your Alpha Assistant. Ask me about risk, budget, or tasks."

    return jsonify({"response": response})


# === IoT Dashboard Routes ===

@app.route('/iot')
def iot_dashboard():
    return render_template('iot_dashboard.html')

@app.route('/api/iot-data')
def iot_data():
    data = {
        "temperature": round(random.uniform(26, 42), 1),
        "humidity": round(random.uniform(30, 80), 1),
        "noise": round(random.uniform(50, 95), 1)
    }
    return jsonify(data)


# === Drone Upload & Gallery Routes ===

import os
from flask import request, redirect, flash
from werkzeug.utils import secure_filename

UPLOAD_FOLDER = os.path.join(app.static_folder, 'drone_uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route('/upload/drone', methods=['GET', 'POST'])
def upload_drone():
    if request.method == 'POST':
        file = request.files.get('file')
        if file:
            filename = secure_filename(file.filename)
            file.save(os.path.join(UPLOAD_FOLDER, filename))
            flash("Image uploaded successfully!", "success")
            return redirect('/gallery/drone')
    return render_template('drone_upload.html')

@app.route('/gallery/drone')
def drone_gallery():
    images = os.listdir(UPLOAD_FOLDER)
    return render_template('drone_gallery.html', images=images)


# === VR/AR Viewer Route ===

@app.route('/vr')
def vr_viewer():
    return render_template('vr_viewer.html')

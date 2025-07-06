import os
from datetime import datetime, timedelta
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from io import BytesIO
from models import User, PurchaseRequest, CashDemand, EmployeeRegistration, ExpenseRecord, ExpenseItem
from app import db

class ReportGenerator:
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self.title_style = ParagraphStyle(
            'CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            spaceAfter=30,
            textColor=colors.HexColor('#1A1A1A'),
            fontName='Helvetica-Bold'
        )
        self.heading_style = ParagraphStyle(
            'CustomHeading',
            parent=self.styles['Heading2'],
            fontSize=16,
            spaceAfter=12,
            textColor=colors.HexColor('#2D2D2D'),
            fontName='Helvetica-Bold'
        )
        self.normal_style = ParagraphStyle(
            'CustomNormal',
            parent=self.styles['Normal'],
            fontSize=11,
            spaceAfter=6,
            textColor=colors.HexColor('#1A1A1A')
        )

    def generate_daily_report(self, date=None):
        """Generate daily report for a specific date"""
        if not date:
            date = datetime.now().date()
        
        # Get data for the specific date
        start_date = datetime.combine(date, datetime.min.time())
        end_date = start_date + timedelta(days=1)
        
        purchases = PurchaseRequest.query.filter(
            PurchaseRequest.submitted_at >= start_date,
            PurchaseRequest.submitted_at < end_date
        ).all()
        
        demands = CashDemand.query.filter(
            CashDemand.submitted_at >= start_date,
            CashDemand.submitted_at < end_date
        ).all()
        
        registrations = EmployeeRegistration.query.filter(
            EmployeeRegistration.submitted_at >= start_date,
            EmployeeRegistration.submitted_at < end_date
        ).all()
        
        expenses = ExpenseRecord.query.filter(
            ExpenseRecord.submitted_at >= start_date,
            ExpenseRecord.submitted_at < end_date
        ).all()
        
        return self._create_report(
            f"Daily Report - {date.strftime('%B %d, %Y')}",
            purchases, demands, registrations, expenses
        )

    def generate_weekly_report(self, week_start=None):
        """Generate weekly report"""
        if not week_start:
            today = datetime.now().date()
            week_start = today - timedelta(days=today.weekday())
        
        week_end = week_start + timedelta(days=7)
        
        start_date = datetime.combine(week_start, datetime.min.time())
        end_date = datetime.combine(week_end, datetime.min.time())
        
        purchases = PurchaseRequest.query.filter(
            PurchaseRequest.submitted_at >= start_date,
            PurchaseRequest.submitted_at < end_date
        ).all()
        
        demands = CashDemand.query.filter(
            CashDemand.submitted_at >= start_date,
            CashDemand.submitted_at < end_date
        ).all()
        
        registrations = EmployeeRegistration.query.filter(
            EmployeeRegistration.submitted_at >= start_date,
            EmployeeRegistration.submitted_at < end_date
        ).all()
        
        expenses = ExpenseRecord.query.filter(
            ExpenseRecord.submitted_at >= start_date,
            ExpenseRecord.submitted_at < end_date
        ).all()
        
        return self._create_report(
            f"Weekly Report - {week_start.strftime('%B %d')} to {(week_end - timedelta(days=1)).strftime('%B %d, %Y')}",
            purchases, demands, registrations, expenses
        )

    def generate_monthly_report(self, year=None, month=None):
        """Generate monthly report"""
        if not year:
            year = datetime.now().year
        if not month:
            month = datetime.now().month
        
        start_date = datetime(year, month, 1)
        if month == 12:
            end_date = datetime(year + 1, 1, 1)
        else:
            end_date = datetime(year, month + 1, 1)
        
        purchases = PurchaseRequest.query.filter(
            PurchaseRequest.submitted_at >= start_date,
            PurchaseRequest.submitted_at < end_date
        ).all()
        
        demands = CashDemand.query.filter(
            CashDemand.submitted_at >= start_date,
            CashDemand.submitted_at < end_date
        ).all()
        
        registrations = EmployeeRegistration.query.filter(
            EmployeeRegistration.submitted_at >= start_date,
            EmployeeRegistration.submitted_at < end_date
        ).all()
        
        expenses = ExpenseRecord.query.filter(
            ExpenseRecord.submitted_at >= start_date,
            ExpenseRecord.submitted_at < end_date
        ).all()
        
        return self._create_report(
            f"Monthly Report - {start_date.strftime('%B %Y')}",
            purchases, demands, registrations, expenses
        )

    def _create_report(self, title, purchases, demands, registrations, expenses):
        """Create PDF report with data"""
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=1*inch)
        story = []
        
        # Title
        story.append(Paragraph(title, self.title_style))
        story.append(Paragraph(f"Generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}", self.normal_style))
        story.append(Spacer(1, 20))
        
        # Summary Statistics
        story.append(Paragraph("Executive Summary", self.heading_style))
        
        total_purchase_amount = sum(p.total_amount for p in purchases if p.status == 'Approved')
        total_demand_amount = sum(d.amount for d in demands if d.status == 'Approved')
        total_expense_amount = 0
        for expense in expenses:
            if expense.status == 'Approved':
                total_expense_amount += sum(item.amount for item in expense.expense_items)
        
        summary_data = [
            ['Metric', 'Count', 'Amount (USD)'],
            ['Purchase Requests', str(len(purchases)), f"${total_purchase_amount:,.2f}"],
            ['Cash Demands', str(len(demands)), f"${total_demand_amount:,.2f}"],
            ['Expense Records', str(len(expenses)), f"${total_expense_amount:,.2f}"],
            ['Employee Registrations', str(len(registrations)), 'N/A'],
            ['Total Financial Impact', '-', f"${total_purchase_amount + total_demand_amount + total_expense_amount:,.2f}"]
        ]
        
        summary_table = Table(summary_data, colWidths=[2.5*inch, 1*inch, 1.5*inch])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2D2D2D')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(summary_table)
        story.append(Spacer(1, 20))
        
        # Build PDF
        doc.build(story)
        buffer.seek(0)
        return buffer

def create_reports_directory():
    """Create reports directory if it doesn't exist"""
    reports_dir = 'reports'
    if not os.path.exists(reports_dir):
        os.makedirs(reports_dir)
    return reports_dir


# === Excel Export Function ===

import io
import xlsxwriter
from flask import send_file

def generate_excel_report():
    output = io.BytesIO()
    workbook = xlsxwriter.Workbook(output, {'in_memory': True})
    worksheet = workbook.add_worksheet("Report")

    headers = ["Project", "Status", "Progress", "Budget", "Deadline"]
    for col, header in enumerate(headers):
        worksheet.write(0, col, header)

    sample_data = [
        ["Project A", "Active", "70%", "$120,000", "2025-09-01"],
        ["Project B", "Delayed", "45%", "$80,000", "2025-12-01"],
        ["Project C", "Completed", "100%", "$200,000", "2025-06-15"]
    ]

    for row, row_data in enumerate(sample_data, start=1):
        for col, value in enumerate(row_data):
            worksheet.write(row, col, value)

    workbook.close()
    output.seek(0)

    return send_file(output,
                     as_attachment=True,
                     download_name="project_report.xlsx",
                     mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

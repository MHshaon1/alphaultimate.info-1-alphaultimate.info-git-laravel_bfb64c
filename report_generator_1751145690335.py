import os
import io
from datetime import datetime, timedelta
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.charts.piecharts import Pie
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics.charts.linecharts import HorizontalLineChart
from io import BytesIO

# Defer matplotlib import to avoid slow startup
def _import_matplotlib():
    import matplotlib
    matplotlib.use('Agg')  # Use non-interactive backend
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates
    return plt, mdates

plt = None
mdates = None
from models import User, PurchaseRequest, CashDemand, EmployeeRegistration, ExpenseRecord, ExpenseItem
from app import db
from sqlalchemy import func

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
            purchases, demands, registrations, expenses,
            f"daily_report_{date.strftime('%Y%m%d')}.pdf"
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
            purchases, demands, registrations, expenses,
            f"weekly_report_{week_start.strftime('%Y%m%d')}.pdf"
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
            purchases, demands, registrations, expenses,
            f"monthly_report_{start_date.strftime('%Y%m')}.pdf"
        )

    def _create_report(self, title, purchases, demands, registrations, expenses, filename):
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
        
        # Status Distribution Chart
        if purchases or demands or expenses:
            story.append(self._create_status_chart(purchases, demands, expenses))
            story.append(Spacer(1, 20))
        
        # Purchase Requests Details
        if purchases:
            story.append(Paragraph("Purchase Requests", self.heading_style))
            purchase_data = [['Item', 'Quantity', 'Unit Price', 'Total', 'Status', 'Urgency']]
            
            for p in purchases:
                purchase_data.append([
                    p.item_name[:30] + ('...' if len(p.item_name) > 30 else ''),
                    str(p.quantity),
                    f"${p.unit_price:.2f}",
                    f"${p.total_amount:.2f}",
                    p.status,
                    p.urgency
                ])
            
            purchase_table = Table(purchase_data, colWidths=[2*inch, 0.7*inch, 0.8*inch, 0.8*inch, 0.8*inch, 0.7*inch])
            purchase_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#00D4AA')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ]))
            
            story.append(purchase_table)
            story.append(Spacer(1, 20))
        
        # Cash Demands Details
        if demands:
            story.append(Paragraph("Cash Demands", self.heading_style))
            demand_data = [['Purpose', 'Amount', 'Department', 'Payment Method', 'Status']]
            
            for d in demands:
                demand_data.append([
                    d.purpose[:35] + ('...' if len(d.purpose) > 35 else ''),
                    f"${d.amount:.2f}",
                    d.department,
                    d.payment_method,
                    d.status
                ])
            
            demand_table = Table(demand_data, colWidths=[2.2*inch, 1*inch, 1.2*inch, 1.2*inch, 0.8*inch])
            demand_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#FFB347')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ]))
            
            story.append(demand_table)
            story.append(Spacer(1, 20))
        
        # Employee Registrations
        if registrations:
            story.append(Paragraph("Employee Registrations", self.heading_style))
            reg_data = [['Name', 'Position', 'Department', 'Start Date', 'Status']]
            
            for r in registrations:
                reg_data.append([
                    f"{r.first_name} {r.last_name}",
                    r.position[:20] + ('...' if len(r.position) > 20 else ''),
                    r.department,
                    r.start_date.strftime('%m/%d/%Y'),
                    r.status
                ])
            
            reg_table = Table(reg_data, colWidths=[1.5*inch, 1.5*inch, 1.2*inch, 1*inch, 0.8*inch])
            reg_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#00C851')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ]))
            
            story.append(reg_table)
            story.append(Spacer(1, 20))
        
        # Expense Records
        if expenses:
            story.append(Paragraph("Expense Records", self.heading_style))
            expense_data = [['Expense ID', 'Department', 'Items', 'Total Amount', 'Status']]
            
            for e in expenses:
                total_amount = sum(item.amount for item in e.expense_items)
                expense_data.append([
                    e.expense_id,
                    e.department,
                    str(len(e.expense_items)),
                    f"${total_amount:.2f}",
                    e.status
                ])
            
            expense_table = Table(expense_data, colWidths=[1.5*inch, 1.2*inch, 0.8*inch, 1.2*inch, 0.8*inch])
            expense_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#FF6B35')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ]))
            
            story.append(expense_table)
        
        # Build PDF
        doc.build(story)
        pdf_data = buffer.getvalue()
        buffer.close()
        
        return pdf_data, filename

    def _create_status_chart(self, purchases, demands, expenses=None):
        """Create status distribution pie chart"""
        global plt, mdates
        if plt is None:
            plt, mdates = _import_matplotlib()
        # Count statuses
        status_counts = {'Pending': 0, 'Approved': 0, 'Rejected': 0}
        
        for p in purchases:
            status_counts[p.status] = status_counts.get(p.status, 0) + 1
        
        for d in demands:
            status_counts[d.status] = status_counts.get(d.status, 0) + 1
        
        if expenses:
            for e in expenses:
                status_counts[e.status] = status_counts.get(e.status, 0) + 1
        
        # Create matplotlib chart
        plt.style.use('dark_background')
        fig, ax = plt.subplots(figsize=(6, 4))
        
        labels = []
        sizes = []
        colors_list = []
        
        color_map = {
            'Pending': '#FFB347',
            'Approved': '#00C851', 
            'Rejected': '#FF4444'
        }
        
        for status, count in status_counts.items():
            if count > 0:
                labels.append(f"{status} ({count})")
                sizes.append(count)
                colors_list.append(color_map[status])
        
        if sizes:
            ax.pie(sizes, labels=labels, colors=colors_list, autopct='%1.1f%%', startangle=90)
            ax.set_title('Request Status Distribution', color='white', fontsize=14, fontweight='bold')
        
        # Save to buffer
        img_buffer = BytesIO()
        plt.savefig(img_buffer, format='PNG', facecolor='#2D2D2D', bbox_inches='tight', dpi=150)
        img_buffer.seek(0)
        plt.close()
        
        # Create ReportLab Image
        img = Image(img_buffer, width=5*inch, height=3*inch)
        return img

def create_reports_directory():
    """Create reports directory if it doesn't exist"""
    reports_dir = os.path.join(os.getcwd(), 'reports')
    if not os.path.exists(reports_dir):
        os.makedirs(reports_dir)
    return reports_dir
import os
from datetime import datetime, timedelta
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from io import BytesIO
from models import PurchaseRequest, CashDemand, EmployeeRegistration, ExpenseRecord

def create_reports_directory():
    """Create reports directory if it doesn't exist"""
    reports_dir = 'reports'
    if not os.path.exists(reports_dir):
        os.makedirs(reports_dir)
    return reports_dir

class ReportGenerator:
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self.title_style = ParagraphStyle(
            'CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=18,
            spaceAfter=30,
            alignment=1  # Center alignment
        )

    def generate_daily_report(self, report_date):
        """Generate daily report for a specific date"""
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        story = []

        # Title
        title = Paragraph(f"Daily Report - {report_date.strftime('%B %d, %Y')}", self.title_style)
        story.append(title)
        story.append(Spacer(1, 12))

        # Get data for the specific date
        start_date = datetime.combine(report_date, datetime.min.time())
        end_date = start_date + timedelta(days=1)

        purchases = PurchaseRequest.query.filter(
            PurchaseRequest.submitted_at >= start_date,
            PurchaseRequest.submitted_at < end_date
        ).all()

        demands = CashDemand.query.filter(
            CashDemand.submitted_at >= start_date,
            CashDemand.submitted_at < end_date
        ).all()

        # Add summary
        summary_data = [
            ['Metric', 'Count', 'Amount'],
            ['Purchase Requests', len(purchases), f"${sum(p.total_amount for p in purchases):.2f}"],
            ['Cash Demands', len(demands), f"${sum(d.amount for d in demands):.2f}"]
        ]

        summary_table = Table(summary_data)
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 14),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))

        story.append(summary_table)
        story.append(Spacer(1, 12))

        doc.build(story)
        pdf_data = buffer.getvalue()
        buffer.close()

        filename = f"daily_report_{report_date.strftime('%Y_%m_%d')}.pdf"
        return pdf_data, filename

    def generate_weekly_report(self, week_start):
        """Generate weekly report"""
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        story = []

        week_end = week_start + timedelta(days=6)
        title = Paragraph(f"Weekly Report - {week_start.strftime('%B %d')} to {week_end.strftime('%B %d, %Y')}", self.title_style)
        story.append(title)

        doc.build(story)
        pdf_data = buffer.getvalue()
        buffer.close()

        filename = f"weekly_report_{week_start.strftime('%Y_%m_%d')}.pdf"
        return pdf_data, filename

    def generate_monthly_report(self, year, month):
        """Generate monthly report"""
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        story = []

        month_name = datetime(year, month, 1).strftime('%B %Y')
        title = Paragraph(f"Monthly Report - {month_name}", self.title_style)
        story.append(title)

        doc.build(story)
        pdf_data = buffer.getvalue()
        buffer.close()

        filename = f"monthly_report_{year}_{month:02d}.pdf"
        return pdf_data, filename

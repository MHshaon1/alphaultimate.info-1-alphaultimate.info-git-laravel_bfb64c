from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, MultipleFileField
from wtforms import StringField, TextAreaField, FloatField, IntegerField, SelectField, DateField, PasswordField, FieldList, FormField, HiddenField
from wtforms.validators import DataRequired, Email, NumberRange, Length

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])

class PurchaseRequestForm(FlaskForm):
    item_name = StringField('Item Name', validators=[DataRequired(), Length(max=200)])
    description = TextAreaField('Description')
    quantity = IntegerField('Quantity', validators=[DataRequired(), NumberRange(min=1)])
    unit_price = FloatField('Unit Price', validators=[DataRequired(), NumberRange(min=0.01)])
    supplier = StringField('Supplier', validators=[Length(max=200)])
    justification = TextAreaField('Business Justification', validators=[DataRequired()])
    urgency = SelectField('Urgency', choices=[
        ('Low', 'Low'),
        ('Normal', 'Normal'),
        ('High', 'High'),
        ('Critical', 'Critical')
    ], default='Normal')

class CashDemandForm(FlaskForm):
    demander_name = StringField('Demander Name', validators=[DataRequired(), Length(max=200)])
    demander_id = StringField('Demander ID', validators=[DataRequired(), Length(max=100)])
    purpose = StringField('Purpose', validators=[DataRequired(), Length(max=200)])
    description = TextAreaField('Description', validators=[DataRequired()])
    amount = FloatField('Amount', validators=[DataRequired(), NumberRange(min=0.01)])
    department = SelectField('Department', choices=[
        ('Finance', 'Finance'),
        ('HR', 'Human Resources'),
        ('IT', 'Information Technology'),
        ('Marketing', 'Marketing'),
        ('Operations', 'Operations'),
        ('Sales', 'Sales'),
        ('Legal', 'Legal'),
        ('Administration', 'Administration')
    ])
    urgency = SelectField('Urgency', choices=[
        ('Low', 'Low'),
        ('Normal', 'Normal'),
        ('High', 'High'),
        ('Critical', 'Critical')
    ], default='Normal')
    payment_method = SelectField('Payment Method', choices=[
        ('Bank Transfer', 'Bank Transfer'),
        ('Cash', 'Cash'),
        ('Check', 'Check'),
        ('Petty Cash', 'Petty Cash')
    ], default='Bank Transfer')

class EmployeeRegistrationForm(FlaskForm):
    first_name = StringField('First Name', validators=[DataRequired(), Length(max=100)])
    last_name = StringField('Last Name', validators=[DataRequired(), Length(max=100)])
    email = StringField('Email', validators=[DataRequired(), Email(), Length(max=120)])
    phone = StringField('Phone Number', validators=[Length(max=20)])
    department = SelectField('Department', choices=[
        ('Finance', 'Finance'),
        ('HR', 'Human Resources'),
        ('IT', 'Information Technology'),
        ('Marketing', 'Marketing'),
        ('Operations', 'Operations'),
        ('Sales', 'Sales'),
        ('Legal', 'Legal'),
        ('Administration', 'Administration')
    ])
    position = StringField('Position', validators=[DataRequired(), Length(max=100)])
    start_date = DateField('Start Date', validators=[DataRequired()])
    salary = FloatField('Salary', validators=[NumberRange(min=0)])
    employee_id = StringField('Employee ID', validators=[Length(max=50)])
    id_number = StringField('ID Number', validators=[Length(max=50)])
    photo = FileField('Photo', validators=[FileAllowed(['jpg', 'jpeg', 'png'], 'Images only!')])
    id_photo = FileField('ID Photo', validators=[FileAllowed(['jpg', 'jpeg', 'png'], 'Images only!')])
    other_files = MultipleFileField('Other Documents', validators=[FileAllowed(['pdf', 'doc', 'docx', 'jpg', 'jpeg', 'png'], 'Documents and images only!')])

class ExpenseItemForm(FlaskForm):
    description = StringField('Description', validators=[DataRequired(), Length(max=500)])
    purpose = StringField('Purpose', validators=[DataRequired(), Length(max=300)])
    quantity = IntegerField('Quantity', validators=[DataRequired(), NumberRange(min=1)])
    rate = FloatField('Rate', validators=[DataRequired(), NumberRange(min=0.01)])
    amount = FloatField('Amount', validators=[DataRequired(), NumberRange(min=0.01)])
    voucher = FileField('Voucher File', validators=[FileAllowed(['pdf', 'jpg', 'jpeg', 'png'], 'PDF or images only!')])

class ExpenseRecordForm(FlaskForm):
    expense_id = StringField('Expense ID', validators=[DataRequired(), Length(max=50)])
    department = SelectField('Department', choices=[
        ('Finance', 'Finance'),
        ('HR', 'Human Resources'),
        ('IT', 'Information Technology'),
        ('Marketing', 'Marketing'),
        ('Operations', 'Operations'),
        ('Sales', 'Sales'),
        ('Legal', 'Legal'),
        ('Administration', 'Administration')
    ])
    # Dynamic items will be added via JavaScript

class ApprovalForm(FlaskForm):
    status = SelectField('Status', choices=[
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected')
    ])
    admin_notes = TextAreaField('Admin Notes')

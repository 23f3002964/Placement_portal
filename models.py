from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy()

class UserAccount(db.Model, UserMixin):
    __tablename__ = 'user_accounts'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)  # User requested NO hashing
    role = db.Column(db.String(20), nullable=False)  # 'admin', 'company', 'student'
    is_active = db.Column(db.Boolean, default=True)
    is_blacklisted = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    student_profile = db.relationship('StudentProfile', backref='user_account', uselist=False, cascade="all, delete-orphan")
    company_profile = db.relationship('CompanyProfile', backref='user_account', uselist=False, cascade="all, delete-orphan")

    def __repr__(self):
        return f'<UserAccount {self.username}>'

class StudentProfile(db.Model):
    __tablename__ = 'student_profiles'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user_accounts.id'), unique=True, nullable=False)
    branch = db.Column(db.String(100))
    cgpa = db.Column(db.Float)
    resume_path = db.Column(db.String(255))
    
    # Relationships
    applications = db.relationship('Application', backref='student_profile', cascade="all, delete-orphan")

    def __repr__(self):
        return f'<StudentProfile {self.id}>'

class CompanyProfile(db.Model):
    __tablename__ = 'company_profiles'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user_accounts.id'), unique=True, nullable=False)
    company_name = db.Column(db.String(150), nullable=False)
    hr_contact = db.Column(db.String(100))
    website = db.Column(db.String(200))
    approval_status = db.Column(db.String(20), default='Pending')  # 'Pending', 'Approved', 'Rejected'
    
    # Relationships
    drives = db.relationship('PlacementDrive', backref='company_profile', cascade="all, delete-orphan")

    def __repr__(self):
        return f'<CompanyProfile {self.company_name}>'

class PlacementDrive(db.Model):
    __tablename__ = 'placement_drives'
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('company_profiles.id'), nullable=False)
    job_title = db.Column(db.String(100), nullable=False)
    job_description = db.Column(db.Text, nullable=False)
    eligibility_criteria = db.Column(db.Text)
    application_deadline = db.Column(db.DateTime)
    status = db.Column(db.String(20), default='Pending')  # 'Pending', 'Approved', 'Closed'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    applications = db.relationship('Application', backref='drive_details', cascade="all, delete-orphan")

    def __repr__(self):
        return f'<PlacementDrive {self.job_title}>'

class Application(db.Model):
    __tablename__ = 'applications'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student_profiles.id'), nullable=False)
    drive_id = db.Column(db.Integer, db.ForeignKey('placement_drives.id'), nullable=False)
    application_date = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='Applied')  # 'Applied', 'Shortlisted', 'Selected', 'Rejected'
    
    # Unique constraint to prevent multiple applications by same student for same drive
    __table_args__ = (db.UniqueConstraint('student_id', 'drive_id', name='_student_drive_uc'),)

    def __repr__(self):
        return f'<Application Student:{self.student_id} Drive:{self.drive_id}>'

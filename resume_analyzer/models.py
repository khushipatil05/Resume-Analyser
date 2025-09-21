import datetime
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import JSON
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin

db = SQLAlchemy()

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    mobile_number = db.Column(db.String(20), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), nullable=False, default='applicant')
    is_verified = db.Column(db.Boolean, default=False)

    # Applicant-specific fields
    graduation_year = db.Column(db.Integer, nullable=True)
    degree = db.Column(db.String(255), nullable=True)

    # Recruiter-specific fields
    official_email = db.Column(db.String(255), nullable=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def is_recruiter(self):
        return self.role == 'recruiter'

class Job(db.Model):
    __tablename__ = 'jobs'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    raw_jd_text = db.Column(db.Text, nullable=True)
    required_skills = db.Column(JSON, nullable=True)
    location = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

    evaluations = db.relationship('Evaluation', back_populates='job')

class Resume(db.Model):
    __tablename__ = 'resumes'
    id = db.Column(db.Integer, primary_key=True)
    applicant_name = db.Column(db.String(255), nullable=True)
    original_file_uri = db.Column(db.String(500), nullable=False)
    raw_text = db.Column(db.Text, nullable=True)
    parsed_text = db.Column(db.Text, nullable=True)
    experience_level = db.Column(db.String(50), nullable=True)
    upload_time = db.Column(db.DateTime, default=datetime.datetime.utcnow)

    evaluations = db.relationship('Evaluation', back_populates='resume')

class Evaluation(db.Model):
    __tablename__ = 'evaluations'
    id = db.Column(db.Integer, primary_key=True)
    resume_id = db.Column(db.Integer, db.ForeignKey('resumes.id'), nullable=False)
    job_id = db.Column(db.Integer, db.ForeignKey('jobs.id'), nullable=False)
    
    hard_score = db.Column(db.Float, nullable=True)
    semantic_score = db.Column(db.Float, nullable=True)
    final_score = db.Column(db.Float, index=True, nullable=True)
    
    verdict = db.Column(db.String(100), nullable=True)
    matched_skills = db.Column(JSON, nullable=True)
    missing_skills = db.Column(JSON, nullable=True)
    suggestions = db.Column(db.Text, nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

    resume = db.relationship('Resume', back_populates='evaluations')
    job = db.relationship('Job', back_populates='evaluations')

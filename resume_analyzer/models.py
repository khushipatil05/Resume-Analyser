import datetime
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import JSON

db = SQLAlchemy()

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

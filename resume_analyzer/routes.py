import os
from flask import Blueprint, request, jsonify, render_template, redirect, url_for
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
from thefuzz import fuzz
from flask_login import login_required, current_user
from sqlalchemy import func

# Local imports
from .parser import extract_text_from_pdf, extract_text_from_docx
from .jd_parser import parse_jd_with_ai, extract_text_from_file as extract_jd_text
from .keyword_extractor import extract_keywords
from .models import db, Job, Resume, Evaluation, User
from .feedback_generator import generate_feedback_from_ai
from .preprocessor import preprocess_text
from .semantic_analyzer import perform_semantic_analysis
from .auth import recruiter_required

# Load environment variables from .env file
load_dotenv()

resumes_bp = Blueprint('resumes', __name__)

# --- Configuration & Constants ---
DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'data'))
UPLOAD_FOLDER = os.path.join(DATA_DIR, 'resumes')
ALLOWED_EXTENSIONS = {'pdf', 'docx'}
FUZZY_MATCH_THRESHOLD = 85
HARD_SCORE_WEIGHT = 0.6
SEMANTIC_SCORE_WEIGHT = 0.4

# --- Helper Functions ---
def ensure_upload_dir_exists():
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# --- Primary Routes ---
@resumes_bp.route('/')
@login_required
def index():
    return redirect(url_for('.dashboard'))

@resumes_bp.route('/dashboard')
@login_required
def dashboard():
    if current_user.role == 'applicant':
        jobs = Job.query.order_by(Job.created_at.desc()).all()
        return render_template('applicant_dashboard.html', jobs=jobs)
    elif current_user.role == 'recruiter':
        jobs = Job.query.filter_by(created_by=current_user.id).order_by(Job.created_at.desc()).all()
        return render_template('recruiter_dashboard.html', jobs=jobs)
    else:
        return "Invalid role", 403

# --- Job Description Parsing ---
@resumes_bp.route('/jd/upload', methods=['POST'])
@login_required
@recruiter_required
def parse_jd_from_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    if file and allowed_file(file.filename):
        jd_text = extract_jd_text(file.stream, file.filename)
        parsed_data = parse_jd_with_ai(jd_text)
        if 'error' in parsed_data:
            return jsonify(parsed_data), 500
        return jsonify(parsed_data), 200
    return jsonify({'error': 'Invalid file type'}), 400

# --- Job Management ---
@resumes_bp.route('/jobs', methods=['POST'])
@login_required
@recruiter_required
def add_job():
    data = request.get_json()
    if not data or not all(k in data for k in ['title', 'description', 'keywords']):
        return jsonify({'error': 'Missing required fields'}), 400
    try:
        new_job = Job(
            title=data['title'],
            raw_jd_text=data['description'],
            required_skills=data['keywords'],
            location=data.get('location'),
            created_by=current_user.id
        )
        db.session.add(new_job)
        db.session.commit()
        return jsonify({'message': 'Job added successfully', 'job': {'id': new_job.id, 'title': new_job.title}}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Database error: {str(e)}'}), 500

# --- Recruiter-Facing Analytics ---
@resumes_bp.route('/job-analytics/<int:job_id>')
@login_required
@recruiter_required
def job_analytics(job_id):
    job = Job.query.get_or_404(job_id)
    
    # Ensure the recruiter can only view analytics for their own jobs
    if job.created_by != current_user.id:
        flash("You are not authorized to view analytics for this job.", "danger")
        return redirect(url_for('.dashboard'))

    evaluations = db.session.query(
        Resume.applicant_name, 
        Evaluation.final_score, 
        Evaluation.verdict
    ).join(Resume, Resume.id == Evaluation.resume_id).filter(Evaluation.job_id == job_id).all()

    total_candidates = len(evaluations)
    if total_candidates == 0:
        return render_template('job_analytics.html', job_title=job.title, total_candidates=0)

    scores = [e.final_score for e in evaluations]
    detailed_analysis = [{
        'name': e.applicant_name, 
        'score': f'{e.final_score:.1f}%', 
        'verdict': e.verdict
    } for e in evaluations]

    return render_template(
        'job_analytics.html',
        job_title=job.title,
        total_candidates=total_candidates,
        shortlisted_candidates=sum(1 for e in evaluations if e.verdict.lower() == 'shortlisted'),
        avg_score=f'{sum(scores) / len(scores):.1f}%',
        top_score=f'{max(scores):.1f}%',
        detailed_analysis=detailed_analysis
    )

# --- Resume & Evaluation ---
@resumes_bp.route('/resumes/upload', methods=['POST'])
@login_required
def upload_resume():
    if 'file' not in request.files or not request.form.get('job_id'):
        return jsonify({'error': 'Missing file or job ID'}), 400

    file = request.files['file']
    job_id = request.form.get('job_id')
    job = Job.query.get(job_id)

    if not job or not allowed_file(file.filename):
        return jsonify({'error': 'Invalid job or file type'}), 400

    raw_text = extract_text_from_pdf(file.stream) if file.filename.endswith('.pdf') else extract_text_from_docx(file.stream)
    
    # Run analysis
    preprocessed_text = preprocess_text(raw_text)
    resume_keywords = extract_keywords(preprocessed_text)
    semantic_score = perform_semantic_analysis(preprocessed_text, job.raw_jd_text)
    matched_skills, missing_skills = find_fuzzy_matches(resume_keywords, job.required_skills)
    hard_score = (len(matched_skills) / len(job.required_skills)) * 100 if job.required_skills else 0
    final_score = (hard_score * HARD_SCORE_WEIGHT) + (semantic_score * SEMANTIC_SCORE_WEIGHT)
    feedback, verdict = generate_feedback_from_ai(raw_text, job.raw_jd_text, final_score)

    # Save to database
    new_resume = Resume(applicant_name=current_user.name, raw_text=raw_text, keywords=resume_keywords, user_id=current_user.id)
    db.session.add(new_resume)
    db.session.commit()

    new_evaluation = Evaluation(resume_id=new_resume.id, job_id=job.id, hard_score=hard_score, semantic_score=semantic_score, final_score=final_score, matched_skills=matched_skills, missing_skills=missing_skills, feedback=feedback, verdict=verdict)
    db.session.add(new_evaluation)
    db.session.commit()

    return jsonify({
        'message': 'Resume analyzed successfully',
        'final_score': final_score,
        'verdict': verdict,
        'feedback': feedback
    }), 201

def find_fuzzy_matches(resume_keywords, job_keywords):
    matched_skills = []
    for job_skill in job_keywords:
        best_match, best_score = None, 0
        for resume_skill in resume_keywords:
            score = fuzz.partial_ratio(job_skill.lower(), resume_skill.lower())
            if score > best_score:
                best_score, best_match = score, resume_skill
        if best_score >= FUZZY_MATCH_THRESHOLD:
            matched_skills.append(job_skill)
    return matched_skills, [k for k in job_keywords if k not in matched_skills]

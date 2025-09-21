import os
from flask import Blueprint, request, jsonify, render_template
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
from thefuzz import fuzz
from flask_login import login_required, current_user
from sqlalchemy import func

# Local imports
from .parser import extract_text_from_pdf, extract_text_from_docx
from .jd_parser import parse_jd_with_ai
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
FUZZY_MATCH_THRESHOLD = 85  # Threshold for fuzzy matching
HARD_SCORE_WEIGHT = 0.6
SEMANTIC_SCORE_WEIGHT = 0.4

# --- Helper Functions ---
def ensure_upload_dir_exists():
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def find_fuzzy_matches(resume_keywords, job_keywords):
    matched_skills = []
    unmatched_job_keywords = list(job_keywords)
    used_resume_keywords = set()

    for job_skill in job_keywords:
        best_match_score = 0
        best_match_resume_skill = None

        for resume_skill in resume_keywords:
            if resume_skill in used_resume_keywords:
                continue
            
            score = fuzz.partial_ratio(job_skill.lower(), resume_skill.lower())
            
            if score > best_match_score:
                best_match_score = score
                best_match_resume_skill = resume_skill
        
        if best_match_score >= FUZZY_MATCH_THRESHOLD:
            matched_skills.append(job_skill)
            if best_match_resume_skill:
                used_resume_keywords.add(best_match_resume_skill)
            if job_skill in unmatched_job_keywords:
                unmatched_job_keywords.remove(job_skill)

    return matched_skills, unmatched_job_keywords

# --- Root Route ---
@resumes_bp.route('/', methods=['GET'])
def index():
    return "Welcome to the Resume Analyzer API!"

# --- Job Description Parsing Route ---
@resumes_bp.route('/jd/parse', methods=['POST'])
@login_required
@recruiter_required
def parse_jd():
    data = request.get_json()
    if not data or 'jd_text' not in data:
        return jsonify({'error': 'No job description text provided'}), 400

    jd_text = data['jd_text']
    if not jd_text.strip():
        return jsonify({'error': 'Job description text is empty'}), 400

    parsed_data = parse_jd_with_ai(jd_text)

    if 'error' in parsed_data:
        return jsonify(parsed_data), 500

    return jsonify(parsed_data), 200

# --- Job Routes ---
@resumes_bp.route('/jobs', methods=['GET'])
@login_required
def get_jobs():
    try:
        jobs = Job.query.order_by(Job.created_at.desc()).all()
        jobs_list = [
            {
                'id': job.id,
                'title': job.title,
                'description': job.raw_jd_text,
                'keywords': job.required_skills,
                'location': job.location
            }
            for job in jobs
        ]
        return jsonify(jobs_list), 200
    except Exception as e:
        return jsonify({'error': f'Failed to fetch jobs: {str(e)}'}), 500

@resumes_bp.route('/jobs', methods=['POST'])
@login_required
@recruiter_required
def add_job():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No input data provided'}), 400

    title = data.get('title')
    description = data.get('description')
    keywords = data.get('keywords')
    location = data.get('location')

    if not all([title, description, keywords]):
        return jsonify({'error': 'Missing required fields: title, description, and keywords are required.'}), 400

    try:
        new_job = Job(
            title=title,
            raw_jd_text=description,
            required_skills=keywords,
            location=location,
            created_by=current_user.id
        )
        db.session.add(new_job)
        db.session.commit()
        return jsonify({
            'message': 'Job added successfully',
            'job': {
                'id': new_job.id,
                'title': new_job.title,
                'description': new_job.raw_jd_text,
                'keywords': new_job.required_skills,
                'location': new_job.location
            }
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Database error: {str(e)}'}), 500

# --- Recruiter-Facing Routes ---
@resumes_bp.route('/evaluations', methods=['GET'])
@login_required
@recruiter_required
def get_evaluations():
    try:
        query = db.session.query(
            Evaluation.id,
            Resume.id.label('resume_id'),
            Resume.applicant_name,
            Job.id.label('job_id'),
            Job.title.label('job_title'),
            Job.location.label('job_location'),
            Resume.experience_level,
            Evaluation.hard_score,
            Evaluation.semantic_score,
            Evaluation.final_score,
            Evaluation.matched_skills,
            Evaluation.missing_skills,
            Evaluation.verdict
        ).join(Resume, Resume.id == Evaluation.resume_id)\
         .join(Job, Job.id == Evaluation.job_id)

        # Filtering logic
        job_id = request.args.get('job_id')
        min_score = request.args.get('min_score')
        location = request.args.get('location')

        if job_id:
            query = query.filter(Job.id == job_id)
        if min_score:
            query = query.filter(Evaluation.final_score >= float(min_score))
        if location:
            query = query.filter(Job.location.ilike(f'%{location}%'))

        evaluations = query.order_by(Evaluation.created_at.desc()).all()

        eval_list = [
            {
                'eval_id': e.id, 
                'resume_id': e.resume_id,
                'applicant_name': e.applicant_name,
                'job_id': e.job_id,
                'job_title': e.job_title,
                'job_location': e.job_location,
                'experience': e.experience_level,
                'score': e.final_score,
                'hard_score': e.hard_score,
                'semantic_score': e.semantic_score,
                'matched_skills': e.matched_skills,
                'missing_skills': e.missing_skills,
                'verdict': e.verdict
            }
            for e in evaluations
        ]
        return jsonify(eval_list), 200
    except Exception as e:
        return jsonify({'error': f'Failed to fetch evaluations: {str(e)}'}), 500

# --- Resume & Evaluation Routes ---
@resumes_bp.route('/resumes/upload', methods=['POST'])
@login_required
def upload_resume():
    ensure_upload_dir_exists()

    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    job_id = request.form.get('job_id')
    if not job_id:
        return jsonify({'error': 'Job ID is required'}), 400

    job = Job.query.get(job_id)
    if not job:
        return jsonify({'error': 'Job not found'}), 404

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(file_path)

        if filename.endswith('.pdf'):
            raw_text = extract_text_from_pdf(file_path)
        elif filename.endswith('.docx'):
            raw_text = extract_text_from_docx(file_path)
        else:
            return jsonify({"error": "Unsupported file type"}), 400

        preprocessed_text = preprocess_text(raw_text)
        resume_keywords = extract_keywords(preprocessed_text)
        semantic_score = perform_semantic_analysis(preprocessed_text, job.raw_jd_text)

        # Fuzzy matching for hard skills
        matched_skills, missing_skills = find_fuzzy_matches(resume_keywords, job.required_skills)
        hard_score = (len(matched_skills) / len(job.required_skills)) * 100 if job.required_skills else 0
        final_score = (hard_score * HARD_SCORE_WEIGHT) + (semantic_score * SEMANTIC_SCORE_WEIGHT)

        # Generate AI-based feedback
        feedback, verdict = generate_feedback_from_ai(raw_text, job.raw_jd_text, final_score)
        
        new_resume = Resume(
            applicant_name=current_user.name,
            raw_text=raw_text,
            keywords=resume_keywords,
            user_id=current_user.id
        )
        db.session.add(new_resume)
        db.session.commit()

        new_evaluation = Evaluation(
            resume_id=new_resume.id,
            job_id=job.id,
            hard_score=hard_score,
            semantic_score=semantic_score,
            final_score=final_score,
            matched_skills=matched_skills,
            missing_skills=missing_skills,
            feedback=feedback,
            verdict=verdict
        )
        db.session.add(new_evaluation)
        db.session.commit()
        
        return jsonify({
            'message': 'Resume uploaded and analyzed successfully',
            'filename': filename,
            'resume_id': new_resume.id,
            'evaluation_id': new_evaluation.id,
            'applicant_name': new_resume.applicant_name,
            'hard_score': hard_score,
            'semantic_score': semantic_score,
            'final_score': final_score,
            'matched_skills': matched_skills,
            'missing_skills': missing_skills,
            'feedback': feedback,
            'verdict': verdict
        }), 201

    return jsonify({'error': 'Invalid file type'}), 400

@resumes_bp.route('/dashboard/<int:job_id>', methods=['GET'])
@login_required
@recruiter_required
def dashboard(job_id):
    job = Job.query.get_or_404(job_id)

    # Query for evaluations for the given job
    evaluations = db.session.query(
        Resume.applicant_name,
        Evaluation.final_score,
        Evaluation.verdict,
        User.email
    ).join(Resume, Resume.id == Evaluation.resume_id).join(User, User.id == Resume.user_id).filter(Evaluation.job_id == job_id).all()

    if not evaluations:
        return jsonify({
            'job_title': job.title,
            'total_candidates': 0,
            'shortlisted_candidates': 0,
            'avg_score': 0,
            'top_score': 0,
            'with_email': 0,
            'score_distribution': {},
            'detailed_analysis': []
        })

    total_candidates = len(evaluations)
    shortlisted_candidates = sum(1 for e in evaluations if e.verdict.lower() == 'shortlisted')
    
    scores = [e.final_score for e in evaluations]
    avg_score = sum(scores) / len(scores) if scores else 0
    top_score = max(scores) if scores else 0
    with_email = sum(1 for e in evaluations if e.email)

    # Calculate score distribution
    score_distribution = {
        '0-20': 0, '21-40': 0, '41-60': 0, '61-80': 0, '81-100': 0
    }
    for score in scores:
        if 0 <= score <= 20:
            score_distribution['0-20'] += 1
        elif 21 <= score <= 40:
            score_distribution['21-40'] += 1
        elif 41 <= score <= 60:
            score_distribution['41-60'] += 1
        elif 61 <= score <= 80:
            score_distribution['61-80'] += 1
        elif 81 <= score <= 100:
            score_distribution['81-100'] += 1

    # Detailed candidate analysis
    detailed_analysis = [
        {
            'name': e.applicant_name,
            'score': f'{e.final_score:.1f}%',
            'verdict': e.verdict
        }
        for e in evaluations
    ]

    dashboard_data = {
        'job_title': job.title,
        'total_candidates': total_candidates,
        'shortlisted_candidates': shortlisted_candidates,
        'avg_score': f'{avg_score:.1f}%',
        'top_score': f'{top_score:.1f}%',
        'with_email': with_email,
        'score_distribution': score_distribution,
        'detailed_analysis': detailed_analysis
    }

    return jsonify(dashboard_data)

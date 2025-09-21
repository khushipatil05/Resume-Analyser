import os
from flask import Blueprint, request, jsonify
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
from thefuzz import fuzz

# Local imports
from .parser import extract_text_from_pdf, extract_text_from_docx
from .jd_parser import parse_jd_with_ai
from .keyword_extractor import extract_keywords
from .models import db, Job, Resume, Evaluation
from .feedback_generator import generate_feedback_from_ai
from .preprocessor import preprocess_text
from .semantic_analyzer import perform_semantic_analysis

# Load environment variables from .env file
load_dotenv()

resumes_bp = Blueprint('resumes_bp', __name__)

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
            location=location
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
# ... (the rest of the file remains the same)

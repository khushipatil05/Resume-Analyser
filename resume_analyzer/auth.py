from flask import Blueprint, render_template, redirect, url_for, request, flash
from resume_analyzer.models import db, User
from resume_analyzer.forms import RegistrationForm, LoginForm
from flask_login import login_user, logout_user, login_required, current_user
from functools import wraps

auth_bp = Blueprint('auth', __name__)

def recruiter_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_recruiter:
            return redirect(url_for('resumes.upload_resume'))
        return f(*args, **kwargs)
    return decorated_function

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        existing_user = User.query.filter(
            (User.email == form.email.data) | (User.mobile_number == form.mobile_number.data)
        ).first()
        if existing_user:
            flash('An account with this email or mobile number already exists.', 'danger')
            return redirect(url_for('auth.register'))

        user = User(
            name=form.name.data,
            email=form.email.data,
            mobile_number=form.mobile_number.data,
            role=form.role.data
        )

        if form.role.data == 'applicant':
            user.graduation_year = form.graduation_year.data
            user.degree = form.degree.data
        else: # Recruiter
            user.official_email = form.official_email.data
        
        # For now, we'll automatically verify the user.
        # In a real application, you would send a verification email.
        user.is_verified = True

        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Your account has been created! You are now able to log in', 'success')
        return redirect(url_for('auth.login'))
    return render_template('register.html', title='Register', form=form)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.check_password(form.password.data):
            if not user.is_verified:
                flash('Please verify your account before logging in. We have sent a verification link to your email.', 'warning')
                return redirect(url_for('auth.login'))

            login_user(user, remember=True)
            flash('You have been logged in!', 'success')
            if user.is_recruiter:
                return redirect(url_for('auth.job_type'))
            else:
                return redirect(url_for('resumes.upload_resume'))
        else:
            flash('Login Unsuccessful. Please check email and password', 'danger')
    return render_template('login.html', title='Login', form=form)

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))

@auth_bp.route('/')
def index():
    return redirect(url_for('auth.login'))

TECHNICAL_JOBS = {
    "Software Development": ["Frontend Developer", "Backend Developer", "Full-Stack Developer"],
    "Data Science": ["Data Analyst", "Data Scientist", "Machine Learning Engineer"],
    "Cybersecurity": ["Security Analyst", "Ethical Hacker", "Security Engineer"],
    "Cloud Computing": ["Cloud Architect", "Cloud Engineer", "SysOps Administrator"],
    "DevOps": ["DevOps Engineer", "Release Manager", "Automation Engineer"]
}

NON_TECHNICAL_JOBS = {
    "Human Resources": ["HR Generalist", "Recruiter", "HR Manager"],
    "Marketing": ["Digital Marketer", "Content Strategist", "SEO Specialist"],
    "Sales": ["Sales Development Representative", "Account Executive", "Sales Manager"],
    "Customer Support": ["Customer Support Representative", "Technical Support Specialist", "Customer Success Manager"],
    "Product Management": ["Product Manager", "Product Owner", "Business Analyst"]
}

@auth_bp.route('/job_type', methods=['GET', 'POST'])
@login_required
@recruiter_required
def job_type():
    if request.method == 'POST':
        job_type = request.form.get('job_type')
        return redirect(url_for('auth.select_domain', job_type=job_type))
    return render_template('job_type.html')

@auth_bp.route('/select_domain', methods=['GET', 'POST'])
@login_required
@recruiter_required
def select_domain():
    job_type = request.args.get('job_type') or request.form.get('job_type')
    
    if job_type == 'Technical':
        domains = list(TECHNICAL_JOBS.keys())
    elif job_type == 'Non-Technical':
        domains = list(NON_TECHNICAL_JOBS.keys())
    else:
        return redirect(url_for('auth.job_type'))

    if request.method == 'POST':
        domain = request.form.get('domain')
        return redirect(url_for('auth.select_job', job_type=job_type, domain=domain))

    return render_template('domain_selection.html', job_type=job_type, domains=domains)

@auth_bp.route('/select_job', methods=['GET', 'POST'])
@login_required
@recruiter_required
def select_job():
    job_type = request.args.get('job_type') or request.form.get('job_type')
    domain = request.args.get('domain') or request.form.get('domain')

    if job_type == 'Technical':
        jobs = TECHNICAL_JOBS.get(domain, [])
    elif job_type == 'Non-Technical':
        jobs = NON_TECHNICAL_JOBS.get(domain, [])
    else:
        return redirect(url_for('auth.job_type'))

    if request.method == 'POST':
        job = request.form.get('job')
        return f"You selected the {job} position in the {domain} domain."

    return render_template('select_job.html', job_type=job_type, domain=domain, jobs=jobs)

@auth_bp.route('/new_job', methods=['GET', 'POST'])
@login_required
@recruiter_required
def new_job():
    # This is a placeholder for the new job description form
    if request.method == 'POST':
        # Process the form data here
        pass
    return render_template('new_job.html')

@auth_bp.route('/dashboard')
@login_required
@recruiter_required
def dashboard_route():
    return render_template('dashboard.html')

from flask import Blueprint, render_template, redirect, url_for, request, flash
from resume_analyzer.models import db, User
from resume_analyzer.forms import RegistrationForm, LoginForm
from flask_login import login_user, logout_user, login_required, current_user
from functools import wraps

auth_bp = Blueprint('auth', __name__)

# --- Decorators ---
def recruiter_required(f):
    """Ensures the logged-in user is a recruiter."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_recruiter:
            flash("You do not have permission to access this page.", "danger")
            return redirect(url_for('resumes.dashboard'))
        return f(*args, **kwargs)
    return decorated_function

# --- Core Authentication Routes ---
@auth_bp.route('/')
def index():
    # Redirect to login, or dashboard if already logged in
    if current_user.is_authenticated:
        return redirect(url_for('resumes.dashboard'))
    return redirect(url_for('auth.login'))

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('resumes.dashboard'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(
            name=form.name.data,
            email=form.email.data,
            mobile_number=form.mobile_number.data,
            role=form.role.data
        )
        user.set_password(form.password.data)
        
        # In a real app, you'd set is_verified to False and email a confirmation link
        user.is_verified = True 

        db.session.add(user)
        db.session.commit()
        
        # Log the user in directly after registration
        login_user(user)
        flash('Your account has been created and you are now logged in!', 'success')
        return redirect(url_for('resumes.dashboard'))
        
    return render_template('register.html', title='Register', form=form)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('resumes.dashboard'))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.check_password(form.password.data):
            if not user.is_verified:
                flash('Please verify your account before logging in.', 'warning')
                return redirect(url_for('auth.login'))

            login_user(user, remember=form.remember.data)
            flash('You have been logged in!', 'success')
            # Redirect all users to the unified dashboard
            return redirect(url_for('resumes.dashboard'))
        else:
            flash('Login unsuccessful. Please check email and password.', 'danger')
            
    return render_template('login.html', title='Login', form=form)

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'success')
    return redirect(url_for('auth.login'))

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
import os

# Local imports
from .models import db, User
from .routes import resumes_bp
from .auth import auth_bp

# Determine the absolute path for the database
data_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'data'))
os.makedirs(data_dir, exist_ok=True)  # Ensure the data directory exists
db_path = os.path.join(data_dir, 'project.db')

def create_app():
    """Creates and configures a Flask application instance."""
    app = Flask(__name__, template_folder='../templates')
    app.config['SECRET_KEY'] = 'your_secret_key'  # Replace with a real secret key

    # --- Database Configuration ---
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # --- Initialize Extensions ---
    db.init_app(app)
    migrate = Migrate(app, db) # Initialize Flask-Migrate
    login_manager = LoginManager(app)
    login_manager.login_view = 'auth.login'

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # --- Register Blueprints ---
    app.register_blueprint(resumes_bp)
    app.register_blueprint(auth_bp)

    with app.app_context():
        db.create_all()  # Create database tables if they don't exist

    return app

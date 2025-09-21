from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import os

# Local imports
from .models import db
from .routes import resumes_bp

# Determine the absolute path for the database
data_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'data'))
os.makedirs(data_dir, exist_ok=True)  # Ensure the data directory exists
db_path = os.path.join(data_dir, 'project.db')

def create_app():
    """Creates and configures a Flask application instance."""
    app = Flask(__name__)

    # --- Database Configuration ---
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # --- Initialize Extensions ---
    db.init_app(app)
    migrate = Migrate(app, db) # Initialize Flask-Migrate

    # --- Register Blueprints ---
    app.register_blueprint(resumes_bp)

    with app.app_context():
        db.create_all()  # Create database tables if they don't exist

    return app

from flask import Flask
from .routes import resumes_bp
from .similarity import similarity_bp

def create_app():
    """Creates and configures the Flask application."""
    app = Flask(__name__)

    # Register the blueprints
    app.register_blueprint(resumes_bp, url_prefix='/resumes')
    app.register_blueprint(similarity_bp, url_prefix='/similarity')

    return app

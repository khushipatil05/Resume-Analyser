import os

from flask import Flask
from resume_analyzer.routes import resumes_bp

def create_app():
    app = Flask(__name__)

    # A simple health check route
    @app.route("/")
    def hello_world():
        """Example Hello World route."""
        return "Resume Analyzer is up and running!"

    # Register the blueprint for resume and JD uploads
    app.register_blueprint(resumes_bp, url_prefix='/api')

    return app

if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
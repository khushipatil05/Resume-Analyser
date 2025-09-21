import os
from flask import Flask, request, jsonify
from flask_migrate import Migrate
from flask_mail import Mail, Message
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Local imports
from resume_analyzer.routes import resumes_bp
from resume_analyzer.models import db, Job, Resume, Evaluation

mail = Mail()

def create_app():
    """Flask application factory."""
    app = Flask(__name__)

    # --- Configuration ---
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv(
        'DATABASE_URL', f"sqlite:///{os.path.join(os.path.dirname(os.path.abspath(__file__)), 'project.db')}"
    )
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # --- Email Configuration ---
    # Use environment variables for sensitive email settings
    app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER', 'smtp.mailtrap.io')
    app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT', 2525))
    app.config['MAIL_USE_TLS'] = os.getenv('MAIL_USE_TLS', 'True').lower() in ['true', 'on', '1']
    app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME', 'your_mailtrap_username') # Replace with your Mailtrap username
    app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD', 'your_mailtrap_password') # Replace with your Mailtrap password
    app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_DEFAULT_SENDER', 'feedback@resume-analyzer.com')

    # --- Extensions ---
    db.init_app(app)
    Migrate(app, db)
    mail.init_app(app)

    # --- Blueprints & Routes ---
    app.register_blueprint(resumes_bp, url_prefix='/api')

    @app.route("/")
    def hello_world():
        return "Resume Analyzer is up and running!"

    @app.route("/api/send_feedback_email", methods=['POST'])
    def send_feedback_email():
        data = request.get_json()
        recipient_email = data.get('email')
        job_title = data.get('job_title')
        feedback = data.get('feedback')

        if not all([recipient_email, job_title, feedback]):
            return jsonify({'error': 'Missing required fields'}), 400

        try:
            msg = Message(
                subject=f"Your Resume Feedback for the {job_title} Position",
                recipients=[recipient_email],
                html=feedback  # Use HTML for better formatting
            )
            mail.send(msg)
            return jsonify({'message': 'Feedback email sent successfully'}), 200
        except Exception as e:
            # Log the error in a real application
            return jsonify({'error': f'Failed to send email: {str(e)}'}), 500

    # --- Shell Context ---
    @app.shell_context_processor
    def make_shell_context():
        return {
            'db': db,
            'Job': Job,
            'Resume': Resume,
            'Evaluation': Evaluation
        }

    return app

if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))

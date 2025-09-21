import json
import os
from main import create_app, db
from resume_analyzer.models import Job

# --- Configuration & Constants ---
DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), 'data'))
JOBS_FILE = os.path.join(DATA_DIR, 'jobs.json')

def seed_jobs():
    """Seeds the database with job listings from the jobs.json file."""
    app = create_app()
    with app.app_context():
        # Check if jobs already exist to prevent duplicates
        if Job.query.count() > 0:
            print("Jobs table is not empty. Aborting seed.")
            return

        try:
            with open(JOBS_FILE, 'r') as f:
                jobs_data = json.load(f)
        except FileNotFoundError:
            print(f"Error: {JOBS_FILE} not found. No data to seed.")
            return
        except json.JSONDecodeError:
            print(f"Error: Could not decode JSON from {JOBS_FILE}.")
            return

        for job_data in jobs_data:
            new_job = Job(
                title=job_data.get('title'),
                raw_jd_text=job_data.get('description'),
                required_skills=job_data.get('keywords'),
                # You can add more fields here as your model evolves
                # good_to_have=job_data.get('good_to_have'), 
                # min_education=job_data.get('min_education'),
            )
            db.session.add(new_job)
        
        try:
            db.session.commit()
            print(f"Successfully seeded {len(jobs_data)} jobs into the database.")
        except Exception as e:
            db.session.rollback()
            print(f"An error occurred during seeding: {e}")

if __name__ == '__main__':
    seed_jobs()


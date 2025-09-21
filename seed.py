
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from lib.models import User, Base

# --- Database Setup ---
engine = create_engine(f"sqlite:///project.db")
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)

# --- Create Tables ---
Base.metadata.create_all(engine)

# --- Seed Data ---
session = DBSession()

# Check if users already exist
if not session.query(User).first():
    # Create a dummy applicant
    applicant = User(name="Test Applicant", email="applicant@test.com", role="applicant")
    applicant.set_password("password")
    session.add(applicant)

    # Create a dummy recruiter
    recruiter = User(name="Test Recruiter", email="recruiter@test.com", role="recruiter")
    recruiter.set_password("password")
    session.add(recruiter)

    session.commit()
    print("Dummy users created successfully!")
else:
    print("Dummy users already exist.")

session.close()

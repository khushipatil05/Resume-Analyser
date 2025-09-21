
import streamlit as st
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from lib.models import User, Base

# --- Database Setup ---
def get_db_session():
    """Creates a new database session."""
    engine = create_engine(f"sqlite:///project.db")
    Base.metadata.bind = engine
    DBSession = sessionmaker(bind=engine)
    return DBSession()

# --- Authentication ---
def login_user(email, password):
    """Validates user credentials and logs them in."""
    session = get_db_session()
    user = session.query(User).filter_by(email=email).first()
    if user and user.check_password(password):
        st.session_state['logged_in'] = True
        st.session_state['user_name'] = user.name
        st.session_state['user_role'] = user.role
        st.success("Logged in successfully!")
        st.experimental_rerun()
    else:
        st.error("Invalid email or password")

def logout_user():
    """Logs the user out."""
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.experimental_rerun()

# --- Main App ---
st.set_page_config(page_title="Resume Analyzer", page_icon="📄", layout="wide")

if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

if not st.session_state['logged_in']:
    st.title("Login to Resume Analyzer")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        login_user(email, password)
else:
    st.sidebar.title(f"Welcome, {st.session_state['user_name']}!")
    st.sidebar.button("Logout", on_click=logout_user)
    
    st.title("Resume Analyzer Dashboard")
    
    if st.session_state['user_role'] == 'recruiter':
        st.header("Recruiter Dashboard")
        # Add recruiter-specific functionalities here
    else:
        st.header("Applicant Dashboard")
        # Add applicant-specific functionalities here

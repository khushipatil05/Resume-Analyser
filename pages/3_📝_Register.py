
import streamlit as st
from sqlalchemy.orm import sessionmaker
from lib.models import User, Base
from sqlalchemy import create_engine

# --- Database Setup ---
def get_db_session():
    engine = create_engine(f"sqlite:///project.db")
    Base.metadata.bind = engine
    DBSession = sessionmaker(bind=engine)
    return DBSession()

# --- Main App ---
st.set_page_config(page_title="Register", page_icon="📝", layout="wide")

st.title("Create a New Account")

name = st.text_input("Name")
email = st.text_input("Email")
password = st.text_input("Password", type="password")
role = st.selectbox("Role", ["applicant", "recruiter"])

if st.button("Register"):
    if name and email and password and role:
        session = get_db_session()
        # Check if user already exists
        if session.query(User).filter_by(email=email).first():
            st.error("An account with this email already exists.")
        else:
            new_user = User(name=name, email=email, role=role)
            new_user.set_password(password)
            session.add(new_user)
            session.commit()
            st.success("Account created successfully! You can now log in.")
    else:
        st.warning("Please fill out all fields.")


import streamlit as st
from sqlalchemy.orm import sessionmaker
from lib.models import User, Base # Assuming models are in lib
from sqlalchemy import create_engine

# --- Database Setup ---
def get_db_session():
    engine = create_engine(f"sqlite:///project.db")
    Base.metadata.bind = engine
    DBSession = sessionmaker(bind=engine)
    return DBSession()

# --- Main App ---
st.set_page_config(page_title="Account Management", page_icon="🔑", layout="wide")

if not st.session_state.get('logged_in'):
    st.warning("Please log in to manage your account.")
    st.stop()

st.title("Account Management")

session = get_db_session()
user = session.query(User).filter_by(email=st.session_state['user_email']).first()

if user:
    st.write(f"**Name:** {user.name}")
    st.write(f"**Email:** {user.email}")
    st.write(f"**Role:** {user.role}")

    st.subheader("Update Your Information")
    new_name = st.text_input("New Name", value=user.name)
    if st.button("Update Name"):
        user.name = new_name
        session.commit()
        st.success("Name updated successfully!")
        st.experimental_rerun()
else:
    st.error("User not found.")

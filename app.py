import streamlit as st
import requests

# The base URL of your Flask API
API_BASE_URL = "http://127.0.0.1:8080/api"

st.title("Automated Resume Relevance Check")

# --- Resume Upload ---
st.header("Upload Resume")
resume_file = st.file_uploader("Choose a resume file", type=["pdf", "docx"], key="resume_uploader")

if resume_file is not None:
    files = {'resume': (resume_file.name, resume_file.getvalue(), resume_file.type)}
    try:
        response = requests.post(f"{API_BASE_URL}/upload/resume", files=files)
        if response.status_code == 200:
            st.success(f"Successfully uploaded and processed: {resume_file.name}")
            st.json(response.json())
        else:
            st.error(f"Error: {response.status_code} - {response.text}")
    except requests.exceptions.RequestException as e:
        st.error(f"Could not connect to the API: {e}")

# --- Job Description Upload ---
st.header("Upload Job Description")
jd_file = st.file_uploader("Choose a JD file", type=["pdf", "docx"], key="jd_uploader")

if jd_file is not None:
    files = {'jd': (jd_file.name, jd_file.getvalue(), jd_file.type)}
    try:
        response = requests.post(f"{API_BASE_URL}/upload/jd", files=files)
        if response.status_code == 200:
            st.success(f"Successfully uploaded and processed: {jd_file.name}")
            st.json(response.json())
        else:
            st.error(f"Error: {response.status_code} - {response.text}")
    except requests.exceptions.RequestException as e:
        st.error(f"Could not connect to the API: {e}")

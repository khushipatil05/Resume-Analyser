import streamlit as st
import requests
import pandas as pd

# --- Configuration & Constants ---
API_BASE_URL = "http://127.0.0.1:8080/api"

# --- Helper Functions ---
@st.cache_data(ttl=300)
def load_jobs_from_api():
    try:
        response = requests.get(f"{API_BASE_URL}/jobs")
        st.cache_data.clear()  # Clear cache to get the latest jobs
        return response.json() if response.status_code == 200 else []
    except requests.exceptions.RequestException:
        return []

@st.cache_data(ttl=60)
def load_evaluations_from_api():
    try:
        response = requests.get(f"{API_BASE_URL}/evaluations")
        st.cache_data.clear()
        return response.json() if response.status_code == 200 else []
    except requests.exceptions.RequestException:
        return []

# --- UI Helper Functions ---

def format_skills_html(skills, color):
    """Formats a list of skills into a colored HTML string."""
    if not isinstance(skills, list):
        return ""
    return ' '.join(f'<span style="color: white; background-color: {color}; border-radius: 5px; padding: 3px 8px; margin: 2px; display: inline-block;">{skill}</span>' for skill in skills)

def get_score_color(score):
    """Returns a color based on the ATS score."""
    if score >= 75:
        return "green"
    elif score >= 60:
        return "orange"
    elif score >= 50:
        return "red"
    return "grey"

# --- UI Functions ---
def show_applicant_view():
    st.header("Applicant Workflow")
    st.info("Upload your resume and get instant feedback!")

    applicant_name = st.text_input("Your Name")
    experience_level = st.selectbox("Your Experience Level", ["Fresher", "Experienced"])
    uploaded_file = st.file_uploader("Upload Your Resume", type=["pdf", "docx"])
    
    # New: Add a job selection dropdown
    jobs = load_jobs_from_api()
    job_options = {job['id']: job['title'] for job in jobs}
    selected_job_id = st.selectbox("Select the Job You're Applying For", options=list(job_options.keys()), format_func=lambda x: job_options[x])

    if st.button("Analyze My Resume"):
        if not all([applicant_name, experience_level, uploaded_file, selected_job_id]):
            st.error("Please fill in all fields and upload your resume.")
            return

        files = {'resume': (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
        payload = {'applicant_name': applicant_name, 'experience_level': experience_level}

        try:
            # 1. Upload the resume
            upload_response = requests.post(f"{API_BASE_URL}/upload/resume", files=files, data=payload)
            if upload_response.status_code != 201:
                st.error(f"Failed to upload resume: {upload_response.text}")
                return
            
            resume_id = upload_response.json().get('resume_id')
            st.success(f"Resume uploaded successfully! Your Resume ID is {resume_id}.")

            # 2. Trigger the keyword match and get feedback
            match_payload = {'resume_id': resume_id, 'job_id': selected_job_id}
            with st.spinner('Analyzing your resume against the job description...'):
                match_response = requests.post(f"{API_BASE_URL}/keyword_match", json=match_payload)

            if match_response.status_code == 201:
                st.balloons()
                st.subheader("Analysis Complete!")
                results = match_response.json()

                st.metric("Your ATS Score", f"{results['ats_score']}%")
                
                st.markdown("### Matched Keywords")
                st.markdown(format_skills_html(results['matched_keywords'], 'green'), unsafe_allow_html=True)
                
                st.markdown("### Missing Keywords")
                st.markdown(format_skills_html(results['missing_keywords'], 'red'), unsafe_allow_html=True)

                st.markdown("### AI-Powered Feedback")
                st.info(results['ai_feedback'])
            else:
                st.error(f"Failed to analyze resume: {match_response.text}")

        except requests.exceptions.RequestException as e:
            st.error(f"An error occurred: {e}")


def show_placement_view():
    st.header("Placement Team Workflow")
    st.subheader("Upload New Job Description")

    job_title = st.text_input("Job Title")
    job_description = st.text_area("Job Description", height=300)
    required_skills = st.text_input("Required Skills (comma-separated)")

    if st.button("Add Job"):
        if not all([job_title, job_description, required_skills]):
            st.error("Please fill in all fields.")
            return

        keywords_list = [k.strip() for k in required_skills.split(',')]
        payload = {
            'title': job_title,
            'description': job_description,
            'keywords': keywords_list
        }

        try:
            response = requests.post(f"{API_BASE_URL}/jobs", json=payload)
            if response.status_code == 201:
                st.success("Job added successfully!")
                st.json(response.json())
                # Force reload of jobs by clearing the cache
                st.cache_data.clear()
            else:
                st.error(f"Failed to add job: {response.text}")
        except requests.exceptions.RequestException as e:
            st.error(f"An error occurred: {e}")


def show_recruiter_dashboard():
    st.header("Recruiter Dashboard")
    evaluations = load_evaluations_from_api()

    if not evaluations:
        st.info("No candidate evaluations found. Please ask applicants to submit their resumes.")
        st.stop()

    df = pd.DataFrame(evaluations)

    # --- Filtering Section ---
    st.sidebar.header("Filter Candidates")
    job_titles = sorted(df['job_title'].unique())
    selected_jobs = st.sidebar.multiselect("Filter by Job Title", options=job_titles, default=[])

    score_ranges = ["All Scores", "75+", "60-74", "50-59", "<50"]
    selected_range = st.sidebar.selectbox("Filter by ATS Score", options=score_ranges)

    # --- Apply Filters ---
    filtered_df = df.copy()
    if selected_jobs:
        filtered_df = filtered_df[filtered_df['job_title'].isin(selected_jobs)]

    if selected_range != "All Scores":
        if selected_range == "75+":
            filtered_df = filtered_df[filtered_df['score'] >= 75]
        elif selected_range == "<50":
             filtered_df = filtered_df[filtered_df['score'] < 50]
        else:
            lower, upper = map(int, selected_range.split('-'))
            filtered_df = filtered_df[(filtered_df['score'] >= lower) & (filtered_df['score'] <= upper)]

    st.metric("Total Candidates", len(df))
    st.metric("Filtered Candidates", len(filtered_df))

    # --- Display Rich Table ---
    # Header
    st.markdown("""
    <style>
    .header {font-weight: bold; text-align: left;}
    .row {border-bottom: 1px solid #eee; padding-top: 10px; padding-bottom: 10px;}
    </style>
    """, unsafe_allow_html=True)

    header_cols = st.columns([1, 2, 1, 1, 3, 3])
    header_cols[0].markdown('<p class="header">Resume ID</p>', unsafe_allow_html=True)
    header_cols[1].markdown('<p class="header">Applicant Name</p>', unsafe_allow_html=True)
    header_cols[2].markdown('<p class="header">ATS Score</p>', unsafe_allow_html=True)
    header_cols[3].markdown('<p class="header">Experience</p>', unsafe_allow_html=True)
    header_cols[4].markdown('<p class="header">Matched Skills</p>', unsafe_allow_html=True)
    header_cols[5].markdown('<p class="header">Missing Skills</p>', unsafe_allow_html=True)

    # Rows
    for _, row in filtered_df.iterrows():
        row_cols = st.columns([1, 2, 1, 1, 3, 3])
        score = row['score']
        score_color = get_score_color(score)

        row_cols[0].write(str(row.get('resume_id', '')))
        row_cols[1].write(row.get('applicant_name', 'N/A'))
        row_cols[2].markdown(f'<b style="color:{score_color};">{score}</b>', unsafe_allow_html=True)
        row_cols[3].write("Fresher" if row['experience'] in ["Fresher", "Not Specified"] else "Experienced")

        matched_skills_html = format_skills_html(row.get('matched_skills'), 'green')
        missing_skills_html = format_skills_html(row.get('missing_skills'), 'red')

        row_cols[4].markdown(matched_skills_html, unsafe_allow_html=True)
        row_cols[5].markdown(missing_skills_html, unsafe_allow_html=True)
        st.markdown('<div class="row"></div>', unsafe_allow_html=True)

# --- Main App & State Management ---
st.set_page_config(layout="wide")
st.title("AI-Powered Hiring Assistant")

if 'page' not in st.session_state:
    st.session_state.page = 'applicant'

# --- Sidebar Navigation ---
st.sidebar.title("Navigation")
page_selection = st.sidebar.radio(
    "Choose a view",
    ('Applicant View', 'Recruiter Dashboard', 'Placement View'),
    key='page_selection_radio'
)

if page_selection == 'Applicant View':
    st.session_state.page = 'applicant'
elif page_selection == 'Recruiter Dashboard':
    st.session_state.page = 'recruiter'
else:
    st.session_state.page = 'placement'

# --- Page Routing ---
if st.session_state.page == 'applicant':
    show_applicant_view()
elif st.session_state.page == 'recruiter':
    show_recruiter_dashboard()
elif st.session_state.page == 'placement':
    show_placement_view()

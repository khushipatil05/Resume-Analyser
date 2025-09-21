import streamlit as st
import requests
import json

# --- Page Configuration ---
st.set_page_config(
    page_title="JD Parser",
    page_icon="📄",
    layout="wide"
)

# --- Constants ---
API_URL = "http://127.0.0.1:8080/api/jd/parse"

# --- Functions ---
def parse_job_description(jd_text):
    """Sends the job description to the back-end API and returns the parsed data."""
    try:
        response = requests.post(API_URL, json={"jd_text": jd_text})
        response.raise_for_status()  # Raise an exception for bad status codes (4xx or 5xx)
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Error communicating with the API: {e}")
        return None

# --- UI Layout ---
st.title("📄 Job Description Parser")
st.markdown("Paste a job description below to extract key information using AI.")

# --- Main Application Flow ---
jd_text_input = st.text_area("Paste the full job description here:", height=300)

if st.button("Parse Job Description"):
    if jd_text_input.strip():
        with st.spinner("AI is analyzing the job description... This may take a moment."):
            parsed_data = parse_job_description(jd_text_input)

        if parsed_data and "error" not in parsed_data:
            st.success("Successfully parsed the job description!")
            
            # Display the extracted information
            st.subheader("Role Title")
            st.write(parsed_data.get("role_title", "Not found"))

            st.subheader("Must-Have Skills")
            must_have = parsed_data.get("must_have_skills", [])
            if must_have:
                for skill in must_have:
                    st.markdown(f"- {skill}")
            else:
                st.write("No must-have skills identified.")

            st.subheader("Good-to-Have Skills")
            good_to_have = parsed_data.get("good_to_have_skills", [])
            if good_to_have:
                for skill in good_to_have:
                    st.markdown(f"- {skill}")
            else:
                st.write("No good-to-have skills identified.")

            st.subheader("Qualifications")
            st.write(parsed_data.get("qualifications", "Not found"))

        elif parsed_data and "error" in parsed_data:
            st.error(f"Failed to parse: {parsed_data.get('details', 'Unknown error')}")
    else:
        st.warning("Please paste a job description before parsing.")

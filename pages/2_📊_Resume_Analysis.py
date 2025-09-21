
import streamlit as st
import pandas as pd
from lib.parser import doc_to_text
from lib.preprocessor import preprocess_text
from lib.keyword_extractor import get_keywords
from lib.semantic_analyzer import analyze_sentiment
from lib.similarity import get_similarity_score


st.set_page_config(page_title="Resume Analysis", page_icon="📊", layout="wide")

if not st.session_state.get('logged_in'):
    st.warning("Please log in to use the Resume Analysis tool.")
    st.stop()

st.title("Resume Analysis")

job_description = st.text_area("Job Description", height=200)


if st.session_state['user_role'] == 'recruiter':
    uploaded_files = st.file_uploader("Upload Resumes (PDF or DOCX)", type=['pdf', 'docx'], accept_multiple_files=True)
else:
     uploaded_files = st.file_uploader("Upload Your Resume (PDF or DOCX)", type=['pdf', 'docx'], accept_multiple_files=False)

if uploaded_files and job_description:
    if st.button("Analyze"):
        if isinstance(uploaded_files, list):
            results = []
            for uploaded_file in uploaded_files:
                resume_text = doc_to_text(uploaded_file)
                preprocessed_resume = preprocess_text(resume_text)
                preprocessed_jd = preprocess_text(job_description)

                resume_keywords = get_keywords(preprocessed_resume)
                jd_keywords = get_keywords(preprocessed_jd)

                similarity_score = get_similarity_score(preprocessed_resume, preprocessed_jd)
                sentiment = analyze_sentiment(preprocessed_resume)

                results.append({
                    "File Name": uploaded_file.name,
                    "Similarity Score": f"{similarity_score:.2f}",
                    "Resume Keywords": ", ".join(resume_keywords),
                    "JD Keywords": ", ".join(jd_keywords),
                    "Sentiment": f"{sentiment:.2f}",
                })
            
            df = pd.DataFrame(results)
            st.dataframe(df)

        else:
            resume_text = doc_to_text(uploaded_files)
            preprocessed_resume = preprocess_text(resume_text)
            preprocessed_jd = preprocess_text(job_description)

            resume_keywords = get_keywords(preprocessed_resume)
            jd_keywords = get_keywords(preprocessed_jd)

            similarity_score = get_similarity_score(preprocessed_resume, preprocessed_jd)
            sentiment = analyze_sentiment(preprocessed_resume)

            st.subheader(f"Analysis for {uploaded_files.name}")
            st.metric("Similarity Score", f"{similarity_score:.2f}")
            st.metric("Sentiment", f"{sentiment:.2f}")

            col1, col2 = st.columns(2)
            with col1:
                st.subheader("Resume Keywords")
                st.write(", ".join(resume_keywords))
            with col2:
                st.subheader("Job Description Keywords")
                st.write(", ".join(jd_keywords))

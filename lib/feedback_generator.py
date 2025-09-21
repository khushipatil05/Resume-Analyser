import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

def generate_feedback_from_ai(resume_text, job_description, experience_level):
    """
    Generates personalized, constructive feedback for a resume using Google's Generative AI.

    Args:
        resume_text (str): The parsed text of the resume.
        job_description (str): The raw text of the job description.
        experience_level (str): The candidate's experience level ('Fresher' or 'Experienced').

    Returns:
        str: AI-generated feedback and suggestions, or an error message.
    """
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        return "Error: GOOGLE_API_KEY not found. Please set it in your .env file."

    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-pro')

        prompt = f"""
        As a professional career coach and expert resume writer, your task is to provide clear, constructive, and actionable feedback on the following resume. The candidate is applying for a job with the description below and has identified as '{experience_level}'.

        **Job Description:**
        ---
        {job_description}
        ---

        **Candidate's Resume:**
        ---
        {resume_text}
        ---

        Please provide your feedback in the following format, using Markdown for clear presentation:

        ### Overall Impression
        Start with a brief, encouraging summary of the resume's strengths and overall suitability for the role.

        ### Areas for Improvement (Actionable Advice)
        - **Clarity & Impact:** Suggest specific ways to make the language more impactful. For example, replacing passive phrases with active verbs or quantifying achievements.
        - **Relevance to Job Description:** Identify any key skills or qualifications from the job description that are missing or not emphasized enough in the resume. Provide concrete examples of how to integrate them.
        - **Formatting and Readability:** Comment on the resume's structure. Is it easy to scan? Are the most important sections (like Experience or Projects) easy to find? Suggest improvements if needed.
        - **For an '{experience_level}' candidate:** Tailor one piece of advice specifically to their experience level. For a fresher, this might be about highlighting projects or internships. For an experienced candidate, it might be about showcasing leadership or strategic impact.

        ### Suggested Next Steps
        Conclude with 1-2 high-priority next steps the candidate should take to improve their resume for this specific job application.
        """

        response = model.generate_content(prompt)
        return response.text

    except Exception as e:
        # In a real app, you'd want to log this error more robustly
        return f"Error communicating with the AI feedback service: {str(e)}"

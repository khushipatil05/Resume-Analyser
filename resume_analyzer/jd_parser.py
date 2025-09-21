import google.generativeai as genai
import os
import json

def configure_genai():
    """Configures the Generative AI model with the Google API key."""
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY environment variable not set.")
    genai.configure(api_key=api_key)

def parse_jd_with_ai(jd_text: str) -> dict:
    """
    Uses a generative AI model to parse a job description and extract key details.

    Args:
        jd_text: The raw text of the job description.

    Returns:
        A dictionary containing the extracted information.
    """
    # Configure the model
    configure_genai()
    model = genai.GenerativeModel('gemini-pro')

    # Define the prompt for the AI model
    prompt = f"""
    Analyze the following job description and extract the specified information.
    Return the output as a valid JSON object with the following keys:
    - "role_title"
    - "must_have_skills" (as a list of strings)
    - "good_to_have_skills" (as a list of strings)
    - "qualifications" (as a single string summarizing the required qualifications)

    Job Description:
    ---
    {jd_text}
    ---
    """

    try:
        # Generate content and clean up the response
        response = model.generate_content(prompt)
        # The response is often wrapped in markdown, so we need to clean it
        clean_response = response.text.strip().replace('```json', '').replace('```', '')
        
        # Parse the JSON string into a Python dictionary
        parsed_data = json.loads(clean_response)
        return parsed_data

    except Exception as e:
        # If parsing fails, return an error structure
        print(f"Error parsing JD with AI: {e}")
        return {
            "error": "Failed to parse the job description using the AI model.",
            "details": str(e)
        }

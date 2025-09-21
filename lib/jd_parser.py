import google.generativeai as genai
import os
import json
import docx
import fitz  # PyMuPDF

def extract_text_from_file(file_stream, filename: str) -> str:
    """
    Extracts text from a file stream (.docx or .pdf).

    Args:
        file_stream: The file stream object to read from.
        filename: The name of the file, used to determine the file type.

    Returns:
        The extracted text as a single string.
    """
    if filename.endswith(".docx"):
        try:
            doc = docx.Document(file_stream)
            return "\n".join([para.text for para in doc.paragraphs])
        except Exception as e:
            print(f"Error reading .docx file: {e}")
            return ""
    elif filename.endswith(".pdf"):
        try:
            # PyMuPDF opens a file stream directly
            pdf_document = fitz.open(stream=file_stream.read(), filetype="pdf")
            text = ""
            for page_num in range(len(pdf_document)):
                page = pdf_document.load_page(page_num)
                text += page.get_text()
            pdf_document.close()
            return text
        except Exception as e:
            print(f"Error reading .pdf file: {e}")
            return ""
    else:
        # For other file types, assume it's plain text
        try:
            return file_stream.read().decode('utf-8')
        except Exception as e:
            print(f"Error reading plain text file: {e}")
            return ""

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

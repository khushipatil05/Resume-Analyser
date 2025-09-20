import fitz  # PyMuPDF
import docx

def extract_text_from_pdf(file_stream):
    """Extracts text from a PDF file."""
    try:
        doc = fitz.open(stream=file_stream.read(), filetype='pdf')
        text = ""
        for page in doc:
            text += page.get_text()
        return text
    except Exception as e:
        print(f"Error extracting text from PDF: {e}")
        return None

def extract_text_from_docx(file_stream):
    """Extracts text from a DOCX file."""
    try:
        doc = docx.Document(file_stream)
        text = ""
        for paragraph in doc.paragraphs:
            text += paragraph.text + "\n"
        return text
    except Exception as e:
        print(f"Error extracting text from DOCX: {e}")
        return None

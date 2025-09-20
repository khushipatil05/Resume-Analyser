import os
import json
from flask import Blueprint, request, jsonify
from .parser import extract_text_from_pdf, extract_text_from_docx
from .embeddings import chunk_text, get_embeddings

resumes_bp = Blueprint('resumes_bp', __name__)

# Define the path for the data directory
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../data')

def ensure_data_dir_exists():
    """Ensures that the data directory exists."""
    os.makedirs(DATA_DIR, exist_ok=True)

def process_and_save_document(file, file_type):
    """Extracts text, chunks it, gets embeddings, and saves everything to a JSON file."""
    if file.filename == '':
        return jsonify({'error': f'No selected {file_type} file'}), 400

    filename = file.filename
    text = ''
    if filename.endswith('.pdf'):
        text = extract_text_from_pdf(file)
    elif filename.endswith('.docx'):
        text = extract_text_from_docx(file)
    else:
        return jsonify({'error': 'Unsupported file type'}), 400

    if not text:
        return jsonify({'error': f'Could not extract text from {filename}'}), 500

    # Chunk the text
    chunks = chunk_text(text)

    # Get embeddings for the chunks
    embeddings = get_embeddings(chunks)

    # Ensure the data directory exists
    ensure_data_dir_exists()

    # Prepare the data for JSON output
    output_data = {
        'filename': filename,
        'original_text': text,
        'chunks': chunks,
        'embeddings': embeddings
    }

    # Save to a JSON file
    output_filename = os.path.join(DATA_DIR, f"{os.path.splitext(filename)[0]}.json")
    with open(output_filename, 'w') as f:
        json.dump(output_data, f, indent=4)

    return jsonify({'message': f'Successfully processed and saved {filename}'}), 200

@resumes_bp.route('/upload/resume', methods=['POST'])
def upload_resume():
    if 'resume' not in request.files:
        return jsonify({'error': 'No resume file found'}), 400
    file = request.files['resume']
    return process_and_save_document(file, 'resume')

@resumes_bp.route('/upload/jd', methods=['POST'])
def upload_jd():
    if 'jd' not in request.files:
        return jsonify({'error': 'No JD file found'}), 400
    file = request.files['jd']
    return process_and_save_document(file, 'jd')

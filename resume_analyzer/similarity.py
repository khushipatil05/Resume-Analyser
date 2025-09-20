import os
import json
import numpy as np
from flask import Blueprint, request, jsonify
from sklearn.metrics.pairwise import cosine_similarity

similarity_bp = Blueprint('similarity_bp', __name__)

# Define the path for the data directory
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../data')

@similarity_bp.route('/similarity_score', methods=['POST'])
def get_similarity_score():
    """Calculates the cosine similarity between a resume and a job description."""
    data = request.get_json()
    resume_filename = data.get('resume_filename')
    jd_filename = data.get('jd_filename')

    if not resume_filename or not jd_filename:
        return jsonify({'error': 'Both resume_filename and jd_filename are required'}), 400

    try:
        # Load the processed data for the resume
        with open(os.path.join(DATA_DIR, f"{os.path.splitext(resume_filename)[0]}.json")) as f:
            resume_data = json.load(f)

        # Load the processed data for the job description
        with open(os.path.join(DATA_DIR, f"{os.path.splitext(jd_filename)[0]}.json")) as f:
            jd_data = json.load(f)

    except FileNotFoundError as e:
        return jsonify({'error': f'File not found: {e.filename}'}), 404

    # Get the embeddings
    resume_embeddings = resume_data.get('embeddings')
    jd_embeddings = jd_data.get('embeddings')

    if not resume_embeddings or not jd_embeddings:
        return jsonify({'error': 'Embeddings not found for one or both documents'}), 500

    # Calculate the cosine similarity
    # We will take the average of the similarity matrix
    similarity_matrix = cosine_similarity(resume_embeddings, jd_embeddings)
    average_similarity = np.mean(similarity_matrix)

    return jsonify({'average_similarity_score': average_similarity}), 200

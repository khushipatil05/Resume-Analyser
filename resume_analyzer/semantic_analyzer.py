import google.generativeai as genai
import numpy as np
import os

def configure_genai():
    """Configures the Generative AI model with the Google API key."""
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY environment variable not set.")
    genai.configure(api_key=api_key)

def get_embedding(text: str, model='models/embedding-001'):
    """
    Generates a vector embedding for the given text using a specified model.

    Args:
        text: The text to be embedded.
        model: The embedding model to use.

    Returns:
        A list of floats representing the embedding.
    """
    configure_genai()
    try:
        return genai.embed_content(model=model, content=text)["embedding"]
    except Exception as e:
        print(f"Error generating embedding: {e}")
        return None

def calculate_cosine_similarity(vec_a, vec_b):
    """
    Calculates the cosine similarity between two vectors and scales it to 0-100.

    Args:
        vec_a: The first vector.
        vec_b: The second vector.

    Returns:
        The similarity score scaled from 0 to 100.
    """
    if vec_a is None or vec_b is None:
        return 0
    
    vec_a = np.array(vec_a)
    vec_b = np.array(vec_b)
    
    # Check for zero vectors
    if np.linalg.norm(vec_a) == 0 or np.linalg.norm(vec_b) == 0:
        return 0

    # Calculate cosine similarity
    cosine_similarity = np.dot(vec_a, vec_b) / (np.linalg.norm(vec_a) * np.linalg.norm(vec_b))
    
    # Scale to 0-100 and ensure it's within bounds
    scaled_score = (cosine_similarity + 1) / 2 * 100
    return max(0, min(100, round(scaled_score)))

def perform_semantic_analysis(resume_text: str, jd_text: str):
    """
    Performs semantic analysis by comparing a resume and a job description.

    Args:
        resume_text: The text of the resume.
        jd_text: The text of the job description.

    Returns:
        An integer score from 0 to 100 representing the semantic match.
    """
    try:
        # Generate embeddings for both texts
        resume_embedding = get_embedding(resume_text)
        jd_embedding = get_embedding(jd_text)
        
        # Calculate and return the similarity score
        semantic_score = calculate_cosine_similarity(resume_embedding, jd_embedding)
        return semantic_score
    except Exception as e:
        print(f"An error occurred during semantic analysis: {e}")
        return 0

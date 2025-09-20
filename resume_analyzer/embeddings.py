import os
import re
import json
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def configure_genai():
    """Configures the Google Generative AI client."""
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY not found in .env file. Please add it.")
    genai.configure(api_key=api_key)

def chunk_text(text):
    """
    Splits text into paragraphs. This is a simple but effective way to
    create meaningful chunks.
    """
    # Split by one or more newlines
    chunks = re.split(r'\n\s*\n', text)
    # Filter out any empty chunks that might result from multiple newlines
    return [chunk.strip() for chunk in chunks if chunk.strip()]

def get_embeddings(text_chunks):
    """
    Generates embeddings for a list of text chunks using Google's AI.
    """
    configure_genai()
    try:
        # Using a model designed for retrieval and document embedding
        result = genai.embed_content(
            model="models/text-embedding-004",
            content=text_chunks,
            task_type="RETRIEVAL_DOCUMENT",
            title="Resume/Job Description"
        )
        return result['embedding']
    except Exception as e:
        print(f"Error generating embeddings: {e}")
        # Return a list of empty lists to match the expected structure
        return [[] for _ in text_chunks]

import re

def preprocess_text(text):
    """Cleans and standardizes the raw text extracted from a resume."""
    if not text:
        return ""

    # 1. Normalize whitespace (tabs, newlines, etc.)
    text = re.sub(r'\s+', ' ', text).strip()

    # 2. Remove page numbers (e.g., "Page 1", "1 of 3")
    text = re.sub(r'Page\s*\d+\s*(of\s*\d+)?', '', text, flags=re.IGNORECASE)
    text = re.sub(r'\b\d+\s*(/|of|-)\s*\d+\b', '', text) # e.g., 1/3

    # 3. Remove common header/footer and non-essential text
    non_essential_patterns = [
        'curriculum vitae', 'resume', 'contact', 'address',
        'personal details', 'references available upon request'
    ]
    for pattern in non_essential_patterns:
        text = re.sub(r'\b' + pattern + r'\b', '', text, flags=re.IGNORECASE)

    # 4. Remove email addresses and phone numbers
    text = re.sub(r'[\w\.-]+@[\w\.-]+', '', text) # Email
    text = re.sub(r'\b(\+?\d{1,2}\s?)?(\(\d{3}\)|\d{3})[\s.-]?\d{3}[\s.-]?\d{4}\b', '', text) # Phone numbers

    # 5. Re-normalize whitespace after removals
    text = re.sub(r'\s{2,}', ' ', text).strip()

    return text

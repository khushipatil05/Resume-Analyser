import re

# A comprehensive list of technical and non-technical skills
# This list can be expanded over time
SKILLS_DB = [
    # Programming Languages
    'python', 'java', 'c++', 'c#', 'javascript', 'typescript', 'go', 'rust', 'php', 'ruby', 'swift', 'kotlin',
    
    # Web Development
    'html', 'css', 'react', 'angular', 'vue.js', 'nodejs', 'express.js', 'django', 'flask', 'asp.net',
    'restful apis', 'graphql', 'webpack', 'babel',

    # Mobile Development
    'ios', 'android', 'react native', 'flutter', 'swiftui', 'xamarin',

    # Databases
    'sql', 'mysql', 'postgresql', 'mongodb', 'redis', 'cassandra', 'sqlite', 'nosql',

    # Cloud & DevOps
    'aws', 'azure', 'google cloud', 'gcp', 'docker', 'kubernetes', 'terraform', 'ansible', 'jenkins', 'ci/cd',
    'serverless', 'microservices', 'aws lambda', 'azure functions',

    # Data Science & Machine Learning
    'pandas', 'numpy', 'scipy', 'scikit-learn', 'tensorflow', 'pytorch', 'keras', 'machine learning', 'deep learning',
    'data analysis', 'data visualization', 'matplotlib', 'seaborn', 'jupyter', 'spark', 'hadoop',

    # Software Engineering & Design
    'agile', 'scrum', 'git', 'svn', 'data structures', 'algorithms', 'design patterns', 'software architecture',

    # Business & Soft Skills
    'project management', 'product management', 'leadership', 'communication', 'teamwork', 'problem solving',
    'critical thinking', 'creativity', 'adaptability', 'time management', 'negotiation', 'conflict resolution',
    'mentoring', 'public speaking', 'strategic planning', 'market analysis', 'business development', 'sales',
    'customer service', 'ux/ui design', 'product design', 'branding', 'marketing', 'seo', 'sem', 'copywriting',
    'content strategy', 'finance', 'recruiting', 'consulting'
]

def extract_keywords(text):
    """
    Extracts keywords from a given text based on the SKILLS_DB.

    Args:
        text (str): The text to extract keywords from.

    Returns:
        list: A list of unique keywords found in the text.
    """
    found_keywords = set()
    text_lower = text.lower()

    for skill in SKILLS_DB:
        # Use word boundaries to avoid matching substrings (e.g., 'C' in 'CSS')
        pattern = r'\b' + re.escape(skill) + r'\b'
        if re.search(pattern, text_lower):
            found_keywords.add(skill)

    return list(found_keywords)

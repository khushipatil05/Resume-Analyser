import os
from resume_analyzer import create_app

app = create_app()

# It's recommended to use environment variables for sensitive data like secret keys.
# For development, a simple key will suffice.
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'a-secret-key-for-development')

if __name__ == '__main__':
    # Run the app on 0.0.0.0 to make it accessible in the development environment
    # and on port 8080 as is common for web services.
    app.run(host='0.0.0.0', port=8080, debug=True)

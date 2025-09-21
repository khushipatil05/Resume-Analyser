#!/bin/bash

# Activate the virtual environment
source .venv/bin/activate

# Run the Flask development server
# The environment will automatically find the `app` object in `app.py`
flask run --host=0.0.0.0 --port=8080

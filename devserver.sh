#!/bin/bash

# Activate the virtual environment
source .venv/bin/activate

# Run the Streamlit app
streamlit run 1_Home.py --server.port 8080

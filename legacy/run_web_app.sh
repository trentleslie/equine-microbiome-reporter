#!/bin/bash

# Run the Flask web application for Equine Microbiome Reporter

echo "Starting Equine Microbiome Reporter Web Application..."
echo "The application will be available at http://localhost:5001"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Activate poetry environment and run the app
poetry run python web_app.py
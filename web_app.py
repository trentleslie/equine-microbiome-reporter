#!/usr/bin/env python3
"""
Flask web application for Equine Microbiome Reporter
Allows users to upload CSV files and generate advanced PDF reports
"""

import os
import tempfile
from datetime import datetime
from pathlib import Path
from flask import Flask, render_template, request, send_file, flash, redirect, url_for
from werkzeug.utils import secure_filename
import pandas as pd
from advanced_pdf_generator import AdvancedMicrobiomeReportGenerator

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'  # Change this in production
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['REPORTS_FOLDER'] = 'generated_reports'

# Create necessary directories
Path(app.config['UPLOAD_FOLDER']).mkdir(exist_ok=True)
Path(app.config['REPORTS_FOLDER']).mkdir(exist_ok=True)

ALLOWED_EXTENSIONS = {'csv'}

def allowed_file(filename):
    """Check if file has allowed extension."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_barcode_columns(csv_path):
    """Extract available barcode columns from CSV file."""
    try:
        df = pd.read_csv(csv_path, nrows=1)
        barcode_cols = [col for col in df.columns if col.startswith('barcode')]
        return sorted(barcode_cols)
    except Exception as e:
        return []

@app.route('/')
def index():
    """Home page with upload form."""
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    """Handle file upload and initial validation."""
    if 'file' not in request.files:
        flash('No file selected', 'error')
        return redirect(url_for('index'))
    
    file = request.files['file']
    if file.filename == '':
        flash('No file selected', 'error')
        return redirect(url_for('index'))
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{timestamp}_{filename}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # Get barcode columns
        barcode_columns = get_barcode_columns(filepath)
        if not barcode_columns:
            flash('No barcode columns found in the CSV file', 'error')
            os.remove(filepath)
            return redirect(url_for('index'))
        
        current_date = datetime.now().strftime('%d.%m.%Y r.')
        return render_template('configure_report.html', 
                             filename=filename, 
                             barcode_columns=barcode_columns,
                             current_date=current_date)
    else:
        flash('Invalid file type. Please upload a CSV file.', 'error')
        return redirect(url_for('index'))

@app.route('/generate_report', methods=['POST'])
def generate_report():
    """Generate the PDF report with provided parameters."""
    try:
        # Get form data
        filename = request.form.get('filename')
        barcode_column = request.form.get('barcode_column')
        patient_name = request.form.get('patient_name', 'Unknown')
        species = request.form.get('species', 'Koń')
        age = request.form.get('age', 'Unknown')
        sample_number = request.form.get('sample_number', 'N/A')
        date_received = request.form.get('date_received', datetime.now().strftime('%d.%m.%Y r.'))
        performed_by = request.form.get('performed_by', 'Laboratory Staff')
        requested_by = request.form.get('requested_by', 'Veterinarian')
        
        # Validate inputs
        if not filename or not barcode_column:
            flash('Missing required parameters', 'error')
            return redirect(url_for('index'))
        
        # File paths
        csv_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        if not os.path.exists(csv_path):
            flash('CSV file not found', 'error')
            return redirect(url_for('index'))
        
        # Generate report
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_filename = f"report_{patient_name.replace(' ', '_')}_{timestamp}.pdf"
        report_path = os.path.join(app.config['REPORTS_FOLDER'], report_filename)
        
        # Patient information
        patient_info = {
            'name': patient_name,
            'species': species,
            'age': age,
            'sample_number': sample_number,
            'date_received': date_received,
            'date_analyzed': datetime.now().strftime('%d.%m.%Y r.'),
            'performed_by': performed_by,
            'requested_by': requested_by
        }
        
        # Generate the report
        generator = AdvancedMicrobiomeReportGenerator(csv_path, barcode_column)
        generator.generate_report(report_path, patient_info)
        
        # Clean up uploaded file
        os.remove(csv_path)
        
        return render_template('report_ready.html', 
                             report_filename=report_filename,
                             patient_name=patient_name)
        
    except Exception as e:
        flash(f'Error generating report: {str(e)}', 'error')
        return redirect(url_for('index'))

@app.route('/download/<filename>')
def download_report(filename):
    """Download the generated PDF report."""
    try:
        report_path = os.path.join(app.config['REPORTS_FOLDER'], filename)
        if os.path.exists(report_path):
            return send_file(report_path, 
                           as_attachment=True,
                           download_name=filename,
                           mimetype='application/pdf')
        else:
            flash('Report file not found', 'error')
            return redirect(url_for('index'))
    except Exception as e:
        flash(f'Error downloading report: {str(e)}', 'error')
        return redirect(url_for('index'))

@app.route('/cleanup')
def cleanup_old_files():
    """Clean up old files (optional admin endpoint)."""
    # This could be scheduled or called manually
    # For now, just a placeholder
    return "Cleanup functionality not implemented yet"

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)
import streamlit as st
import pandas as pd
import numpy as np
import json
import os
from datetime import datetime
import io
import base64
from io import BytesIO
import plotly.graph_objects as go
import tempfile
import re
from fpdf import FPDF

def parse_file_contents(uploaded_file):
    """Parse uploaded file contents into a DataFrame"""
    # Get file extension
    file_extension = uploaded_file.name.split('.')[-1].lower()
    
    try:
        if file_extension == 'csv':
            # Try to parse as CSV
            df = pd.read_csv(uploaded_file)
            return df
        elif file_extension == 'txt':
            # Try different parsing strategies for TXT files
            content = uploaded_file.getvalue().decode('utf-8')
            
            # Try parsing as CSV first
            try:
                df = pd.read_csv(io.StringIO(content))
                if not df.empty:
                    return df
            except:
                pass
            
            # Try parsing as TSV
            try:
                df = pd.read_csv(io.StringIO(content), sep='\t')
                if not df.empty:
                    return df
            except:
                pass
            
            # Try to detect format based on content
            lines = content.strip().split('\n')
            if len(lines) > 0:
                # Try to detect delimiter
                potential_delimiters = [',', '\t', '|', ';']
                max_field_count = 0
                best_delimiter = ','
                
                for delimiter in potential_delimiters:
                    field_count = len(lines[0].split(delimiter))
                    if field_count > max_field_count:
                        max_field_count = field_count
                        best_delimiter = delimiter
                
                # Try to parse with detected delimiter
                try:
                    df = pd.read_csv(io.StringIO(content), sep=best_delimiter)
                    if not df.empty:
                        return df
                except:
                    pass
                
                # Last resort: try custom parsing for different benchmark formats
                # Try parsing FPS data in custom format (e.g., "Test: Game A - 1080p, Avg FPS: 120.5, 1% Low: 98.3")
                pattern = re.compile(r'([^:,]+):\s*([^,]+)')
                
                data = []
                record = {}
                
                for line in lines:
                    if line.strip() == '':
                        if record:
                            data.append(record)
                            record = {}
                        continue
                    
                    matches = pattern.findall(line)
                    for key, value in matches:
                        key = key.strip()
                        value = value.strip()
                        record[key] = value
                
                # Add the last record if present
                if record:
                    data.append(record)
                
                if data:
                    return pd.DataFrame(data)
                
                # Try parsing space-separated data
                data = []
                for line in lines:
                    if line.strip() and not line.startswith('#'):
                        parts = line.split()
                        if len(parts) >= 2:
                            try:
                                # Assume first part is test name, second is score
                                test_name = parts[0]
                                score = float(parts[1])
                                data.append({'Test': test_name, 'Score': score})
                            except ValueError:
                                pass
                
                if data:
                    return pd.DataFrame(data)
            
            # If all else fails
            st.error("Could not parse the file format. Please check the file or try a different file.")
            return None
        else:
            st.error("Unsupported file format. Please upload a CSV or TXT file.")
            return None
    except Exception as e:
        st.error(f"Error parsing file: {str(e)}")
        return None

def save_session_data():
    """Save session data to the session state storage"""
    # Convert DataFrame to JSON for storage
    if not st.session_state.tests.empty:
        # Store the data in the session state
        st.session_state.data_json = st.session_state.tests.to_json(orient='split')
        
        # Create a timestamp for the last save
        st.session_state.last_saved = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def load_session_data():
    """Load session data from the session state storage"""
    if 'data_json' in st.session_state and st.session_state.data_json:
        try:
            # Load data from the session state
            st.session_state.tests = pd.read_json(st.session_state.data_json, orient='split')
        except Exception as e:
            st.error(f"Error loading session data: {str(e)}")
            st.session_state.tests = pd.DataFrame()

def export_to_csv(df):
    """Export the DataFrame to a CSV file"""
    if not df.empty:
        # Convert DataFrame to CSV
        csv = df.to_csv(index=False)
        
        # Create a download link
        b64 = base64.b64encode(csv.encode()).decode()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"benchmark_data_{timestamp}.csv"
        href = f'<a href="data:file/csv;base64,{b64}" download="{filename}">Download CSV File</a>'
        st.markdown(href, unsafe_allow_html=True)
    else:
        st.error("No data to export.")

def export_to_png():
    """Export current chart as a PNG image"""
    try:
        for key, val in st.session_state.items():
            if isinstance(val, go.Figure):
                # Convert the figure to an image
                img_bytes = val.to_image(format="png", scale=2)
                
                # Create a download link
                b64 = base64.b64encode(img_bytes).decode()
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"benchmark_chart_{timestamp}.png"
                href = f'<a href="data:image/png;base64,{b64}" download="{filename}">Download Chart Image</a>'
                st.markdown(href, unsafe_allow_html=True)
                return
        
        st.warning("No chart found to export. Please generate a chart first.")
    except Exception as e:
        st.error(f"Error exporting chart: {str(e)}")

def export_to_pdf(df):
    """Export the data and charts to a PDF report"""
    if not df.empty:
        try:
            # Create a FPDF object
            pdf = FPDF()
            pdf.add_page()
            
            # Set up the PDF
            pdf.set_font("Arial", size=12)
            
            # Add title
            pdf.set_font("Arial", 'B', 16)
            pdf.cell(200, 10, "Benchmark Report", ln=True, align='C')
            pdf.ln(10)
            
            # Add timestamp
            pdf.set_font("Arial", size=10)
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            pdf.cell(200, 10, f"Generated: {timestamp}", ln=True)
            pdf.ln(5)
            
            # Add data table
            pdf.set_font("Arial", 'B', 12)
            pdf.cell(200, 10, "Benchmark Data", ln=True)
            pdf.ln(5)
            
            # Table header
            pdf.set_font("Arial", 'B', 10)
            col_width = 190 / len(df.columns)
            
            for col in df.columns:
                pdf.cell(col_width, 10, col, border=1)
            pdf.ln()
            
            # Table data
            pdf.set_font("Arial", size=10)
            for _, row in df.iterrows():
                for col in df.columns:
                    pdf.cell(col_width, 10, str(row[col]), border=1)
                pdf.ln()
            
            pdf.ln(10)
            
            # Add info about viewing mode
            view_mode = st.session_state.get('view_mode', 'FPS')
            pdf.set_font("Arial", 'B', 12)
            pdf.cell(200, 10, f"Viewing Mode: {view_mode}", ln=True)
            
            # Generate temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp:
                pdf_output = pdf.output(dest='S').encode('latin1')
                tmp.write(pdf_output)
                tmp_path = tmp.name
            
            # Read the file and create a download link
            with open(tmp_path, 'rb') as f:
                pdf_bytes = f.read()
            
            # Create download link
            b64 = base64.b64encode(pdf_bytes).decode()
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"benchmark_report_{timestamp}.pdf"
            href = f'<a href="data:application/pdf;base64,{b64}" download="{filename}">Download PDF Report</a>'
            st.markdown(href, unsafe_allow_html=True)
            
            # Clean up the temporary file
            os.unlink(tmp_path)
            
        except Exception as e:
            st.error(f"Error generating PDF: {str(e)}")
    else:
        st.error("No data to export to PDF.")

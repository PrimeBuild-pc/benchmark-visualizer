import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from PIL import Image
import base64
from io import BytesIO
import os
import io
import json
from datetime import datetime

from utils import set_page_config, apply_custom_css, load_image_url
from data_handler import (
    parse_file_contents, 
    save_session_data, 
    load_session_data,
    export_to_csv,
    export_to_png,
    export_to_pdf
)
from chart_builder import (
    build_bar_chart, 
    build_line_chart, 
    build_stacked_bar_chart,
    highlight_best_performance
)

# Set page config and apply custom styles
set_page_config()
apply_custom_css()

# Initialize session state
if 'theme' not in st.session_state:
    st.session_state.theme = 'dark'
if 'tests' not in st.session_state:
    st.session_state.tests = pd.DataFrame()
if 'view_mode' not in st.session_state:
    st.session_state.view_mode = 'FPS'
if 'chart_type' not in st.session_state:
    st.session_state.chart_type = 'bar'
if 'column_mapping' not in st.session_state:
    st.session_state.column_mapping = {}
if 'highlight_best' not in st.session_state:
    st.session_state.highlight_best = True

# Load saved session data
load_session_data()

# App header with logo
col1, col2 = st.columns([1, 5])
with col1:
    try:
        # Load from local file instead of URL
        from PIL import Image
        logo = Image.open("generated-icon.png")
        st.image(logo, width=80)
    except Exception as e:
        st.error(f"Error loading local logo: {str(e)}")
with col2:
    st.title("Benchmark Visualizer")

# Sidebar for controls and settings
with st.sidebar:
    st.header("Settings")
    
    # Theme toggle
    theme = st.radio("Theme", ["Dark", "Light"], 
                    index=0 if st.session_state.theme == 'dark' else 1,
                    horizontal=True)
    st.session_state.theme = 'dark' if theme == "Dark" else 'light'
    
    # View mode selection
    view_mode = st.radio("View Mode", ["FPS Mode", "Points Mode"], 
                         index=0 if st.session_state.view_mode == 'FPS' else 1,
                         horizontal=True)
    st.session_state.view_mode = 'FPS' if view_mode == "FPS Mode" else 'Points'
    
    # Chart type selection
    chart_type = st.selectbox("Chart Type", 
                             ["Horizontal Bar Chart", "Line Chart", "Stacked Bar Chart"],
                             index=0 if st.session_state.chart_type == 'bar' else 
                                   1 if st.session_state.chart_type == 'line' else 2)
    
    if chart_type == "Horizontal Bar Chart":
        st.session_state.chart_type = 'bar'
    elif chart_type == "Line Chart":
        st.session_state.chart_type = 'line'
    else:
        st.session_state.chart_type = 'stacked'
    
    # Additional settings
    st.session_state.highlight_best = st.checkbox("Highlight Best Performance", 
                                                value=st.session_state.highlight_best)
    
    # Export options
    st.subheader("Export")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Export PNG"):
            export_to_png()
    with col2:
        if st.button("Export CSV"):
            export_to_csv(st.session_state.tests)
    
    if st.button("Export PDF"):
        export_to_pdf(st.session_state.tests)
    
    # Clear data button
    if st.button("Clear All Data", type="primary"):
        st.session_state.tests = pd.DataFrame()
        st.rerun()

# Main content area
tabs = st.tabs(["Visualization", "Data Input", "Import Data"])

# Tab 1: Visualization
with tabs[0]:
    # Search/filter
    if not st.session_state.tests.empty:
        st.text_input("Search/Filter Tests", key="search_filter", 
                     placeholder="Type to filter tests...")
        
        # Filter based on search term if present
        filtered_df = st.session_state.tests
        if st.session_state.search_filter:
            search_term = st.session_state.search_filter.lower()
            if 'Test' in filtered_df.columns:
                mask = filtered_df['Test'].str.lower().str.contains(search_term, na=False)
                filtered_df = filtered_df[mask]
        
        # Display the chart based on view mode and chart type
        if st.session_state.view_mode == 'FPS':
            fps_metrics = ['Avg FPS', '1% Low', 'Max FPS', 'Min FPS', '0.1% Low']
            available_metrics = [col for col in fps_metrics if col in filtered_df.columns]
            
            if available_metrics:
                selected_metric = st.selectbox("Select Metric to Visualize", available_metrics)
                
                if st.session_state.chart_type == 'bar':
                    fig = build_bar_chart(filtered_df, 'Test', selected_metric, st.session_state.theme)
                elif st.session_state.chart_type == 'line':
                    fig = build_line_chart(filtered_df, 'Test', selected_metric, st.session_state.theme)
                else:
                    fig = build_stacked_bar_chart(filtered_df, 'Test', available_metrics, st.session_state.theme)
                
                if st.session_state.highlight_best and st.session_state.chart_type == 'bar':
                    highlight_best_performance(fig, filtered_df, 'Test', selected_metric)
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Multi-metric comparison
                if len(available_metrics) > 1 and st.checkbox("Show All Metrics Comparison"):
                    for metric in available_metrics:
                        if metric != selected_metric:
                            if st.session_state.chart_type == 'bar':
                                fig = build_bar_chart(filtered_df, 'Test', metric, st.session_state.theme)
                            elif st.session_state.chart_type == 'line':
                                fig = build_line_chart(filtered_df, 'Test', metric, st.session_state.theme)
                            
                            if st.session_state.highlight_best and st.session_state.chart_type == 'bar':
                                highlight_best_performance(fig, filtered_df, 'Test', metric)
                                
                            st.subheader(metric)
                            st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("No FPS metrics found in the data. Please ensure your data contains FPS metrics.")
                
        else:  # Points mode
            if 'Test' in filtered_df.columns and 'Score' in filtered_df.columns:
                if st.session_state.chart_type == 'bar':
                    fig = build_bar_chart(filtered_df, 'Test', 'Score', st.session_state.theme)
                elif st.session_state.chart_type == 'line':
                    fig = build_line_chart(filtered_df, 'Test', 'Score', st.session_state.theme)
                else:
                    # In points mode, stacked doesn't make much sense, fallback to bar
                    fig = build_bar_chart(filtered_df, 'Test', 'Score', st.session_state.theme)
                
                if st.session_state.highlight_best and st.session_state.chart_type == 'bar':
                    highlight_best_performance(fig, filtered_df, 'Test', 'Score')
                
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("No Score data found. Please ensure your data contains Test and Score columns.")
    else:
        st.info("No data available. Please add data through the 'Data Input' or 'Import Data' tabs.")

# Tab 2: Data Input
with tabs[1]:
    st.subheader("Manual Data Entry")
    
    # Create form based on view mode
    with st.form(key="data_entry_form"):
        test_name = st.text_input("Test Name/Label", key="test_name")
        
        if st.session_state.view_mode == 'FPS':
            avg_fps = st.number_input("Average FPS", min_value=0.0, step=0.1, format="%.1f")
            low_1_pct = st.number_input("1% Low", min_value=0.0, step=0.1, format="%.1f")
            max_fps = st.number_input("Max FPS", min_value=0.0, step=0.1, format="%.1f")
            min_fps = st.number_input("Min FPS", min_value=0.0, step=0.1, format="%.1f")
            low_01_pct = st.number_input("0.1% Low", min_value=0.0, step=0.1, format="%.1f")
        else:  # Points mode
            score = st.number_input("Score", min_value=0.0, step=0.1, format="%.1f")
        
        submit_button = st.form_submit_button("Add Data")
        
        if submit_button:
            if not test_name:
                st.error("Test name cannot be empty.")
            else:
                # Create new row
                if st.session_state.view_mode == 'FPS':
                    new_data = {
                        'Test': test_name,
                        'Avg FPS': avg_fps,
                        '1% Low': low_1_pct,
                        'Max FPS': max_fps,
                        'Min FPS': min_fps,
                        '0.1% Low': low_01_pct
                    }
                else:  # Points mode
                    new_data = {
                        'Test': test_name,
                        'Score': score
                    }
                
                # Add to session state
                if st.session_state.tests.empty:
                    st.session_state.tests = pd.DataFrame([new_data])
                else:
                    st.session_state.tests = pd.concat([st.session_state.tests, pd.DataFrame([new_data])], 
                                                      ignore_index=True)
                
                # Save data and refresh
                save_session_data()
                st.success(f"Added test: {test_name}")
                st.rerun()
    
    # Display current data
    if not st.session_state.tests.empty:
        st.subheader("Current Data")
        st.dataframe(st.session_state.tests, use_container_width=True)
        
        # Rename test functionality
        st.subheader("Rename Test")
        col1, col2 = st.columns(2)
        with col1:
            test_options = st.session_state.tests['Test'].unique().tolist()
            test_to_rename = st.selectbox("Select Test to Rename", test_options)
        with col2:
            new_name = st.text_input("New Name")
        
        if st.button("Rename"):
            if new_name:
                st.session_state.tests.loc[st.session_state.tests['Test'] == test_to_rename, 'Test'] = new_name
                save_session_data()
                st.success(f"Renamed test from '{test_to_rename}' to '{new_name}'")
                st.rerun()
            else:
                st.error("New name cannot be empty")

# Tab 3: Import Data
with tabs[2]:
    st.subheader("Import Data from File")
    
    # File upload
    uploaded_file = st.file_uploader("Choose a CSV or TXT file", type=['csv', 'txt'])
    
    if uploaded_file is not None:
        try:
            # Parse file
            df = parse_file_contents(uploaded_file)
            
            if df is not None and not df.empty:
                st.success("File uploaded successfully!")
                st.dataframe(df, use_container_width=True)
                
                # Column mapping for FPS mode
                if st.session_state.view_mode == 'FPS':
                    st.subheader("Map Columns")
                    cols = df.columns.tolist()
                    
                    # If we haven't already mapped columns
                    if not st.session_state.column_mapping:
                        # Try to guess mappings based on column names
                        mapping = {}
                        metrics = ['Test', 'Avg FPS', '1% Low', 'Max FPS', 'Min FPS', '0.1% Low']
                        
                        for metric in metrics:
                            # Look for exact matches or close matches
                            if metric in cols:
                                mapping[metric] = metric
                            else:
                                # Try to find similar columns
                                lower_cols = [col.lower() for col in cols]
                                metric_lower = metric.lower()
                                
                                if 'test' in metric_lower and any('test' in col for col in lower_cols):
                                    for col in cols:
                                        if 'test' in col.lower() or 'name' in col.lower() or 'label' in col.lower():
                                            mapping[metric] = col
                                            break
                                elif 'avg' in metric_lower and any('avg' in col.lower() for col in lower_cols):
                                    for col in cols:
                                        if 'avg' in col.lower() and 'fps' in col.lower():
                                            mapping[metric] = col
                                            break
                                elif '1%' in metric_lower and any('1%' in col for col in lower_cols):
                                    for col in cols:
                                        if '1%' in col and 'low' in col.lower():
                                            mapping[metric] = col
                                            break
                                elif 'max' in metric_lower and any('max' in col.lower() for col in lower_cols):
                                    for col in cols:
                                        if 'max' in col.lower() and 'fps' in col.lower():
                                            mapping[metric] = col
                                            break
                                elif 'min' in metric_lower and any('min' in col.lower() for col in lower_cols):
                                    for col in cols:
                                        if 'min' in col.lower() and 'fps' in col.lower():
                                            mapping[metric] = col
                                            break
                                elif '0.1%' in metric_lower and any('0.1%' in col for col in lower_cols):
                                    for col in cols:
                                        if '0.1%' in col and 'low' in col.lower():
                                            mapping[metric] = col
                                            break
                        
                        st.session_state.column_mapping = mapping
                    
                    # Allow user to adjust mappings
                    col_mapping = {}
                    metrics = ['Test', 'Avg FPS', '1% Low', 'Max FPS', 'Min FPS', '0.1% Low']
                    
                    for metric in metrics:
                        default_idx = cols.index(st.session_state.column_mapping.get(metric, cols[0])) if metric in st.session_state.column_mapping else 0
                        col_mapping[metric] = st.selectbox(f"Map '{metric}' to", options=["None"] + cols, 
                                                         index=default_idx + 1 if metric in st.session_state.column_mapping else 0)
                    
                    # Store the mappings
                    for metric, col in col_mapping.items():
                        if col != "None":
                            st.session_state.column_mapping[metric] = col
                
                # Import Button
                if st.button("Import Data"):
                    # Process the dataframe according to the view mode
                    if st.session_state.view_mode == 'FPS':
                        # Create a new dataframe with the mapped columns
                        new_df = pd.DataFrame()
                        
                        for metric, col in st.session_state.column_mapping.items():
                            if col != "None" and col in df.columns:
                                new_df[metric] = df[col]
                        
                        # Check if we have at least Test and one metric
                        if 'Test' in new_df.columns and len(new_df.columns) > 1:
                            # Add to existing data or create new
                            if st.session_state.tests.empty:
                                st.session_state.tests = new_df.copy()
                            else:
                                # Make sure columns match
                                for col in new_df.columns:
                                    if col not in st.session_state.tests.columns:
                                        st.session_state.tests[col] = np.nan
                                
                                st.session_state.tests = pd.concat([st.session_state.tests, new_df], ignore_index=True)
                            
                            save_session_data()
                            st.success("Data imported successfully!")
                            st.rerun()
                        else:
                            st.error("Need at least Test column and one metric.")
                    else:  # Points mode
                        # For points mode, we need 'Test' and 'Score' columns
                        if 'Test' not in df.columns and len(df.columns) >= 2:
                            # Try to guess: first column is often the test name
                            df = df.rename(columns={df.columns[0]: 'Test'})
                        
                        if 'Score' not in df.columns and len(df.columns) >= 2:
                            # Try to guess: second column is often the score
                            for col in df.columns:
                                if col != 'Test':
                                    df = df.rename(columns={col: 'Score'})
                                    break
                        
                        if 'Test' in df.columns and 'Score' in df.columns:
                            # Keep only the needed columns
                            new_df = df[['Test', 'Score']].copy()
                            
                            # Add to existing data or create new
                            if st.session_state.tests.empty:
                                st.session_state.tests = new_df.copy()
                            else:
                                st.session_state.tests = pd.concat([st.session_state.tests, new_df], ignore_index=True)
                            
                            save_session_data()
                            st.success("Data imported successfully!")
                            st.rerun()
                        else:
                            st.error("Could not identify Test and Score columns.")
                
                # Reset mappings button
                if st.session_state.view_mode == 'FPS' and st.button("Reset Column Mappings"):
                    st.session_state.column_mapping = {}
                    st.rerun()
                    
        except Exception as e:
            st.error(f"Error processing file: {str(e)}")
    
    st.markdown("### Drag & Drop")
    st.info("You can also drag and drop CSV or TXT files directly onto the file uploader above.")
    
    st.markdown("### Sample File Format")
    if st.session_state.view_mode == 'FPS':
        sample_csv = """Test,Avg FPS,1% Low,Max FPS,Min FPS,0.1% Low
Game A - 1080p,120.5,98.3,142.1,75.6,67.2
Game B - 1080p,95.2,75.1,110.3,62.8,55.1
"""
    else:
        sample_csv = """Test,Score
Benchmark A,10250
Benchmark B,8750
"""
    
    st.code(sample_csv, language="csv")
    st.caption("Note: The app will attempt to automatically map columns if their names are similar to the expected format.")

# Auto-save session when app closes or is refreshed
save_session_data()

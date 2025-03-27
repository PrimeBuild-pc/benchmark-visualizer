import streamlit as st
from PIL import Image
import requests
from io import BytesIO
import base64

def set_page_config():
    """Set up the page configuration"""
    st.set_page_config(
        page_title="Benchmark Visualizer",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="expanded",
    )

def apply_custom_css():
    """Apply custom CSS for dark mode and styling"""
    # Define CSS for dark and light themes
    dark_theme_css = """
    <style>
        /* Dark theme styles */
        [data-testid="stSidebar"] {
            background-color: #1E1E1E;
        }
        .stApp {
            background-color: #121212;
            color: white;
        }
        .stButton button {
            border-radius: 6px;
        }
        button[data-baseweb="tab"] {
            color: #ff7514 !important;
        }
        button[data-baseweb="tab"][aria-selected="true"] {
            color: #ff7514 !important;
            border-bottom-color: #ff7514 !important;
        }
        .stTabs [data-baseweb="tab-list"] {
            gap: 8px;
        }
        header {
            background-color: #1E1E1E !important;
        }
        /* Primary buttons */
        .stButton > button[data-baseweb="button"] {
            background-color: #ff7514;
            color: white;
        }
    </style>
    """
    
    light_theme_css = """
    <style>
        /* Light theme styles */
        [data-testid="stSidebar"] {
            background-color: #f5f5f5;
        }
        .stApp {
            background-color: white;
            color: #333333;
        }
        .stButton button {
            border-radius: 6px;
        }
        button[data-baseweb="tab"] {
            color: #ff7514 !important;
        }
        button[data-baseweb="tab"][aria-selected="true"] {
            color: #ff7514 !important;
            border-bottom-color: #ff7514 !important;
        }
        .stTabs [data-baseweb="tab-list"] {
            gap: 8px;
        }
        header {
            background-color: #f5f5f5 !important;
        }
        /* Primary buttons */
        .stButton > button[data-baseweb="button"] {
            background-color: #ff7514;
            color: white;
        }
    </style>
    """
    
    # Apply CSS based on theme
    if st.session_state.get('theme', 'dark') == 'dark':
        st.markdown(dark_theme_css, unsafe_allow_html=True)
    else:
        st.markdown(light_theme_css, unsafe_allow_html=True)

def load_image_url(url):
    """Load an image from a URL"""
    try:
        response = requests.get(url)
        img = Image.open(BytesIO(response.content))
        return img
    except Exception as e:
        st.error(f"Error loading image: {str(e)}")
        return None

def get_image_base64(img):
    """Convert PIL image to base64 string"""
    buffered = BytesIO()
    img.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()
    return img_str

"""
Precision Oncology Therapy Targeting System

A streamlit application for precision oncology that identifies optimal therapy levels
and provides treatment recommendations for cancer patients based on their molecular profiles.
Currently supports breast cancer and lung cancer.
"""

import streamlit as st
from config import app_config
from utils.ai_integration import initialize_azure_openai
from utils.data_loader import load_knowledge_base, load_patient_data
from modules.patient_lookup import render_patient_lookup
from modules.dashboard import render_dashboard
from modules.database import render_database
from modules.new_patient import render_new_patient

# Set up page configuration
st.set_page_config(
    page_title=app_config.APP_TITLE,
    page_icon=app_config.APP_ICON,
    layout=app_config.APP_LAYOUT
)

def main():
    """
    Main application function
    """
    # Initialize Azure OpenAI client
    openai_client = initialize_azure_openai()
    
    # Application header
    st.title(f"{app_config.APP_ICON} {app_config.APP_TITLE}")
    st.markdown("""
    This application helps identify the optimal therapy level and specific treatment 
    recommendations for cancer patients based on their molecular profiles.
    """)
    
    # Add cancer type selection
    cancer_type = st.sidebar.radio(
        "Select Cancer Type:",
        app_config.CANCER_TYPES
    )
    
    # Load the knowledge base for the selected cancer type
    knowledge_base = load_knowledge_base(cancer_type)  # Pass the cancer_type parameter here
    if knowledge_base is None:
        st.error(f"Failed to load the therapy knowledge base for {cancer_type}. Please ensure the file exists.")
        return
    
    # Load the patient data for the selected cancer type
    try:
        patient_data, raw_data = load_patient_data(cancer_type)
        if patient_data is None or raw_data is None:
            st.error(f"Failed to load patient data for {cancer_type}. Please ensure the file exists.")
            return
    except Exception as e:
        st.error(f"Error processing {cancer_type} patient data: {e}")
        return
        
    # Create tabs for the application
    tabs = st.tabs(app_config.TABS)
    
    # Render each tab
    with tabs[0]:
        render_patient_lookup(patient_data, knowledge_base, openai_client, cancer_type)
    
    with tabs[1]:
        render_dashboard(patient_data, raw_data, cancer_type)
    
    with tabs[2]:
        render_database(patient_data, raw_data, cancer_type)
    
    with tabs[3]:
        render_new_patient(knowledge_base, openai_client, cancer_type)

if __name__ == "__main__":
    main()
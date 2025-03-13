"""
Functions for loading data files
"""

import os
import json
import pandas as pd
import streamlit as st
from config import app_config
from utils.data_processor import process_breast_cancer_data, process_lung_cancer_data
from modules.lung_cancer import create_default_lung_knowledge_base
from modules.breast_cancer import create_default_breast_knowledge_base

@st.cache_data
def load_knowledge_base(cancer_type):
    """
    Load the therapy knowledge base from JSON file based on cancer type

    Args:
        cancer_type: Type of cancer ("Breast Cancer" or "Lung Cancer")

    Returns:
        Dictionary with therapy knowledge base data or None if error
    """
    # Choose the correct knowledge base file path
    if cancer_type == "Breast Cancer":
        file_path = app_config.BREAST_CANCER_KNOWLEDGE_BASE_PATH
    else:  # Lung Cancer
        file_path = app_config.LUNG_CANCER_KNOWLEDGE_BASE_PATH
    
    try:
        with open(file_path, 'r') as f:
            knowledge_base = json.load(f)
        return knowledge_base
    except Exception as e:
        st.error(f"Error loading knowledge base for {cancer_type}: {e}")
        # Create and return a default knowledge base based on cancer type
        if cancer_type == "Breast Cancer":
            return create_default_breast_knowledge_base()
        else:  # Lung Cancer
            return create_default_lung_knowledge_base()

@st.cache_data
def load_patient_data(cancer_type):
    """
    Load and process the cancer patient data file

    Args:
        cancer_type: Type of cancer to load data for ("Breast Cancer" or "Lung Cancer")

    Returns:
        Tuple of (processed_patient_dataframe, raw_data_dataframe) or (None, None) if error
    """
    # Choose the correct patient data file path
    if cancer_type == "Breast Cancer":
        file_path = app_config.BREAST_CANCER_PATIENT_DATA_PATH
    else:  # Lung Cancer
        file_path = app_config.LUNG_CANCER_PATIENT_DATA_PATH
    
    if not os.path.exists(file_path):
        st.error(f"Data file {file_path} not found for {cancer_type}.")
        return None, None
    
    # Load the TSV file
    try:
        raw_data = pd.read_csv(file_path, sep='\t')
        
        # Process the data based on cancer type
        if cancer_type == "Breast Cancer":
            return process_breast_cancer_data(raw_data)
        else:  # Lung Cancer
            return process_lung_cancer_data(raw_data)
    except Exception as e:
        st.error(f"Error loading patient data for {cancer_type}: {e}")
        return None, None
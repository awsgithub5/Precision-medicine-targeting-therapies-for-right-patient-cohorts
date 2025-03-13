"""
Database tab functionality for the Precision Oncology application
"""

import streamlit as st
import pandas as pd
from config import app_config

def render_database(patient_data, raw_data, cancer_type):
    """
    Render the Database tab

    Args:
        patient_data: DataFrame with patient data
        raw_data: Raw dataframe from TSV file
        cancer_type: Type of cancer ("Breast Cancer" or "Lung Cancer")
    """
    if cancer_type == "Breast Cancer":
        render_breast_cancer_database(patient_data, raw_data)
    else:  # Lung Cancer
        render_lung_cancer_database(patient_data, raw_data)

def render_breast_cancer_database(patient_data, raw_data):
    """
    Render the breast cancer specific database

    Args:
        patient_data: DataFrame with patient data
        raw_data: Raw dataframe from TSV file
    """
    st.header("Breast Cancer Patient Database")
    
    # Allow filtering
    st.subheader("Filter Patients")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Filter by subtype
        subtypes = sorted(patient_data['breast_cancer_subtype'].unique())
        selected_subtypes = st.multiselect(
            "Cancer Subtypes:",
            options=subtypes,
            default=subtypes
        )
    
    with col2:
        # Filter by therapy level
        levels = sorted(patient_data['optimal_therapy_level'].unique())
        selected_levels = st.multiselect(
            "Therapy Levels:",
            options=levels,
            default=levels
        )
    
    with col3:
        # Filter by genes
        genes = sorted(raw_data['track_name'].unique())
        selected_gene = st.selectbox(
            "Filter by Gene Alteration:",
            options=["All"] + genes
        )
    
    # Apply filters
    filtered_data = patient_data.copy()
    
    if selected_subtypes:
        filtered_data = filtered_data[filtered_data['breast_cancer_subtype'].isin(selected_subtypes)]
    
    if selected_levels:
        filtered_data = filtered_data[filtered_data['optimal_therapy_level'].isin(selected_levels)]
    
    if selected_gene != "All":
        gene_filter = (
            filtered_data['gene_amplifications'].apply(lambda x: selected_gene in x) | 
            filtered_data['gene_deletions'].apply(lambda x: selected_gene in x) |
            filtered_data['gene_mutations'].apply(lambda x: any(selected_gene in mut for mut in x))
        )
        # Add expression filters if these columns exist
        if 'high_expression' in filtered_data.columns:
            gene_filter = gene_filter | filtered_data['high_expression'].apply(lambda x: selected_gene in x)
        if 'low_expression' in filtered_data.columns:
            gene_filter = gene_filter | filtered_data['low_expression'].apply(lambda x: selected_gene in x)
            
        filtered_data = filtered_data[gene_filter]
    
    # Display number of patients after filtering
    st.write(f"Showing {len(filtered_data)} patients")
    
    # Create a simplified view for display
    display_data = pd.DataFrame({
        'Patient ID': filtered_data.index,
        'Subtype': filtered_data['breast_cancer_subtype'],
        'Therapy Level': filtered_data['optimal_therapy_level'],
        'Gene Amplifications': filtered_data['gene_amplifications'].apply(lambda x: ', '.join(x) if len(x) > 0 else 'None'),
        'Gene Mutations Count': filtered_data['gene_mutations'].apply(lambda x: len(x)),
        'High Expression Genes Count': filtered_data['high_expression'].apply(lambda x: len(x)) if 'high_expression' in filtered_data.columns else pd.Series([0] * len(filtered_data))
    })
    
    # Display the data
    st.dataframe(display_data, use_container_width=True)
    
    # Option to export data
    if st.button("Export Filtered Data to CSV"):
        csv = display_data.to_csv(index=False)
        st.download_button(
            label="Download CSV",
            data=csv,
            file_name="filtered_breast_cancer_data.csv",
            mime="text/csv"
        )

def render_lung_cancer_database(patient_data, raw_data):
    """
    Render the lung cancer specific database

    Args:
        patient_data: DataFrame with patient data
        raw_data: Raw dataframe from TSV file
    """
    st.header("Lung Cancer Patient Database")
    
    # Allow filtering
    st.subheader("Filter Patients")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Filter by subtype
        subtypes = sorted(patient_data['lung_cancer_subtype'].dropna().unique())
        selected_subtypes = st.multiselect(
            "Cancer Subtypes:",
            options=subtypes,
            default=subtypes
        )
    
    with col2:
        # Filter by therapy level
        levels = sorted(patient_data['optimal_therapy_level'].dropna().unique())
        selected_levels = st.multiselect(
            "Therapy Levels:",
            options=levels,
            default=levels
        )
    
    with col3:
        # Filter by genes
        genes = sorted([g for g in raw_data['track_name'].unique() 
                      if g not in ['Study of origin', 'Profiled for copy number alterations', 
                                  'Profiled for mutations', 'Profiled for structural variants']])
        selected_gene = st.selectbox(
            "Filter by Gene Alteration:",
            options=["All"] + genes
        )
    
    # Apply filters
    filtered_data = patient_data.copy()
    
    if selected_subtypes:
        filtered_data = filtered_data[filtered_data['lung_cancer_subtype'].isin(selected_subtypes)]
    
    if selected_levels:
        filtered_data = filtered_data[filtered_data['optimal_therapy_level'].isin(selected_levels)]
    
    if selected_gene != "All":
        gene_filter = (
            filtered_data['gene_amplifications'].apply(lambda x: selected_gene in x) | 
            filtered_data['gene_deletions'].apply(lambda x: selected_gene in x) |
            filtered_data['gene_mutations'].apply(lambda x: any(selected_gene in mut for mut in x))
        )
        
        # Add structural variant filter if this column exists
        if 'structural_variants' in filtered_data.columns:
            gene_filter = gene_filter | filtered_data['structural_variants'].apply(
                lambda x: any(selected_gene in sv for sv in x)
            )
            
        filtered_data = filtered_data[gene_filter]
    
    # Display number of patients after filtering
    st.write(f"Showing {len(filtered_data)} patients")
    
    # Create a simplified view for display
    display_data = pd.DataFrame({
        'Patient ID': filtered_data.index,
        'Cancer Type': filtered_data['study_of_origin'].apply(lambda x: 'LUAD' if 'Adenocarcinoma' in str(x) else ('LUSC' if 'Squamous' in str(x) else 'Unknown')),
        'Molecular Subtype': filtered_data['lung_cancer_subtype'],
        'Therapy Level': filtered_data['optimal_therapy_level'],
        'Gene Amplifications': filtered_data['gene_amplifications'].apply(lambda x: ', '.join(x) if len(x) > 0 else 'None'),
        'Gene Mutations Count': filtered_data['gene_mutations'].apply(lambda x: len(x)),
        'Structural Variants Count': filtered_data['structural_variants'].apply(lambda x: len(x)) if 'structural_variants' in filtered_data.columns else pd.Series([0] * len(filtered_data))
    })
    
    # Display the data
    st.dataframe(display_data, use_container_width=True)
    
    # Option to export data
    if st.button("Export Filtered Data to CSV"):
        csv = display_data.to_csv(index=False)
        st.download_button(
            label="Download CSV",
            data=csv,
            file_name="filtered_lung_cancer_data.csv",
            mime="text/csv"
        )
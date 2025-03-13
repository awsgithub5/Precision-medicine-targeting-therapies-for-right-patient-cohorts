"""
Dashboard tab functionality for the Precision Oncology application
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from modules.lung_cancer import get_lung_cancer_key_alterations

def render_dashboard(patient_data, raw_data, cancer_type):
    """
    Render the Dashboard tab

    Args:
        patient_data: DataFrame with patient data
        raw_data: Raw dataframe from TSV file
        cancer_type: Type of cancer ("Breast Cancer" or "Lung Cancer")
    """
    if cancer_type == "Breast Cancer":
        render_breast_cancer_dashboard(patient_data, raw_data)
    else:  # Lung Cancer
        render_lung_cancer_dashboard(patient_data, raw_data)

def render_breast_cancer_dashboard(patient_data, raw_data):
    """
    Render the breast cancer specific dashboard

    Args:
        patient_data: DataFrame with patient data
        raw_data: Raw dataframe from TSV file
    """
    st.header("Breast Cancer Analytics Dashboard")
    
    # Create columns for the charts
    col1, col2 = st.columns(2)
    
    with col1:
        # Distribution of molecular subtypes
        st.subheader("Distribution of Breast Cancer Subtypes")
        subtype_counts = patient_data['breast_cancer_subtype'].value_counts()
        
        # Create a bar chart using Plotly
        fig = px.bar(
            x=subtype_counts.index, 
            y=subtype_counts.values,
            labels={'x': 'Subtype', 'y': 'Number of Patients'},
            color=subtype_counts.index,
            color_discrete_map={
                'Luminal A/B': '#3498db',
                'Luminal HER2+': '#9b59b6',
                'HER2 Enriched': '#e74c3c',
                'Triple Negative': '#2ecc71'
            }
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Distribution of therapy levels
        st.subheader("Distribution of Therapy Levels")
        therapy_counts = patient_data['optimal_therapy_level'].value_counts().sort_index()
        
        # Create a bar chart using Plotly
        fig = px.bar(
            x=[f"Level {i}" for i in therapy_counts.index], 
            y=therapy_counts.values,
            labels={'x': 'Therapy Level', 'y': 'Number of Patients'},
            color=therapy_counts.index,
            color_discrete_sequence=['#3498db', '#9b59b6', '#e74c3c', '#2ecc71']
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # Therapy level distribution by subtype
    st.subheader("Therapy Levels by Cancer Subtype")
    
    # Create a cross-tabulation of subtype vs therapy level
    subtype_therapy = pd.crosstab(
        patient_data['breast_cancer_subtype'], 
        patient_data['optimal_therapy_level'],
        normalize='index'
    ) * 100
    
    # Convert to long format for plotting
    subtype_therapy_long = subtype_therapy.reset_index().melt(
        id_vars=['breast_cancer_subtype'],
        var_name='Therapy Level',
        value_name='Percentage'
    )
    
    # Create a stacked bar chart
    fig = px.bar(
        subtype_therapy_long,
        x='breast_cancer_subtype',
        y='Percentage',
        color='Therapy Level',
        labels={'breast_cancer_subtype': 'Cancer Subtype', 'Therapy Level': 'Therapy Level'},
        title='Distribution of Therapy Levels by Cancer Subtype',
        color_discrete_map={1: '#3498db', 2: '#9b59b6', 3: '#e74c3c', 4: '#2ecc71'}
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # Common genomic alterations
    st.subheader("Common Genomic Alterations")
    
    # Count frequency of gene amplifications
    amp_genes = []
    for amps in patient_data['gene_amplifications']:
        amp_genes.extend(amps)
    
    if amp_genes:  # Check if the list is not empty
        amp_counts = pd.Series(amp_genes).value_counts().head(10)
    else:
        amp_counts = pd.Series([])
    
    # Count frequency of gene mutations
    mut_genes = []
    for muts in patient_data['gene_mutations']:
        mut_genes.extend([m.split(':')[0] for m in muts])
    
    if mut_genes:  # Check if the list is not empty
        mut_counts = pd.Series(mut_genes).value_counts().head(10)
    else:
        mut_counts = pd.Series([])
    
    # Display as two columns
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Top 10 Amplified Genes**")
        
        if not amp_counts.empty:
            # Create a bar chart
            fig = px.bar(
                x=amp_counts.index,
                y=amp_counts.values,
                labels={'x': 'Gene', 'y': 'Frequency'},
                color=amp_counts.index,
                color_discrete_sequence=px.colors.qualitative.Pastel
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No gene amplification data available")
    
    with col2:
        st.markdown("**Top 10 Mutated Genes**")
        
        if not mut_counts.empty:
            # Create a bar chart
            fig = px.bar(
                x=mut_counts.index,
                y=mut_counts.values,
                labels={'x': 'Gene', 'y': 'Frequency'},
                color=mut_counts.index,
                color_discrete_sequence=px.colors.qualitative.Pastel
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No gene mutation data available")

def render_lung_cancer_dashboard(patient_data, raw_data):
    """
    Render the lung cancer specific dashboard

    Args:
        patient_data: DataFrame with patient data
        raw_data: Raw dataframe from TSV file
    """
    st.header("Lung Cancer Analytics Dashboard")
    
    # Create columns for the charts
    col1, col2 = st.columns(2)
    
    with col1:
        # Distribution of molecular subtypes
        st.subheader("Distribution of Lung Cancer Subtypes")
        
        # Filter valid subtypes (exclude Unknown or NaN)
        valid_subtypes = patient_data['lung_cancer_subtype'].dropna()
        valid_subtypes = valid_subtypes[valid_subtypes != "Unknown"]
        
        subtype_counts = valid_subtypes.value_counts()
        
        # Create a bar chart using Plotly
        fig = px.bar(
            x=subtype_counts.index, 
            y=subtype_counts.values,
            labels={'x': 'Subtype', 'y': 'Number of Patients'},
            color=subtype_counts.index,
            color_discrete_sequence=px.colors.qualitative.Bold
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Distribution of therapy levels
        st.subheader("Distribution of Therapy Levels")
        therapy_counts = patient_data['optimal_therapy_level'].value_counts().sort_index()
        
        # Create a bar chart using Plotly
        fig = px.bar(
            x=[f"Level {i}" for i in therapy_counts.index], 
            y=therapy_counts.values,
            labels={'x': 'Therapy Level', 'y': 'Number of Patients'},
            color=therapy_counts.index,
            color_discrete_sequence=px.colors.qualitative.Pastel
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # Therapy level distribution by subtype
    st.subheader("Therapy Levels by Cancer Subtype")
    
    # Filter for main subtypes to make the chart more readable
    main_subtypes = ['LUAD EGFR-mutated', 'LUAD ALK-rearranged', 'LUAD KRAS-mutated', 'LUAD Other', 'LUSC']
    filtered_data = patient_data[patient_data['lung_cancer_subtype'].isin(main_subtypes)]
    
    # Create a cross-tabulation of subtype vs therapy level
    subtype_therapy = pd.crosstab(
        filtered_data['lung_cancer_subtype'], 
        filtered_data['optimal_therapy_level'],
        normalize='index'
    ) * 100
    
    # Convert to long format for plotting
    subtype_therapy_long = subtype_therapy.reset_index().melt(
        id_vars=['lung_cancer_subtype'],
        var_name='Therapy Level',
        value_name='Percentage'
    )
    
    # Create a stacked bar chart
    fig = px.bar(
        subtype_therapy_long,
        x='lung_cancer_subtype',
        y='Percentage',
        color='Therapy Level',
        labels={'lung_cancer_subtype': 'Cancer Subtype', 'Therapy Level': 'Therapy Level'},
        title='Distribution of Therapy Levels by Cancer Subtype',
        color_discrete_map={1: '#3498db', 2: '#9b59b6', 3: '#e74c3c', 4: '#2ecc71'}
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # Common genomic alterations
    st.subheader("Common Genomic Alterations")
    
    # Count frequency of gene amplifications
    amp_genes = []
    for amps in patient_data['gene_amplifications']:
        amp_genes.extend(amps)
    
    if amp_genes:  # Check if the list is not empty
        amp_counts = pd.Series(amp_genes).value_counts().head(10)
    else:
        amp_counts = pd.Series([])
    
    # Count frequency of gene mutations
    mut_genes = []
    for muts in patient_data['gene_mutations']:
        # Extract just the gene name before the colon
        mut_genes.extend([m.split(':')[0] for m in muts if ':' in m])
    
    if mut_genes:  # Check if the list is not empty
        mut_counts = pd.Series(mut_genes).value_counts().head(10)
    else:
        mut_counts = pd.Series([])
    
    # Display as two columns
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Top Amplified Genes**")
        
        if not amp_counts.empty:
            # Create a bar chart
            fig = px.bar(
                x=amp_counts.index,
                y=amp_counts.values,
                labels={'x': 'Gene', 'y': 'Frequency'},
                color=amp_counts.index,
                color_discrete_sequence=px.colors.qualitative.Pastel
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No gene amplification data available")
    
    with col2:
        st.markdown("**Top Mutated Genes**")
        
        if not mut_counts.empty:
            # Create a bar chart
            fig = px.bar(
                x=mut_counts.index,
                y=mut_counts.values,
                labels={'x': 'Gene', 'y': 'Frequency'},
                color=mut_counts.index,
                color_discrete_sequence=px.colors.qualitative.Pastel
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No gene mutation data available")
            
    # Distribution of EGFR, ALK, ROS1, and KRAS alterations
    st.subheader("Key Driver Alterations in Lung Cancer")
    
    # Get key alterations counts
    driver_counts = get_lung_cancer_key_alterations(patient_data)
    
    fig = px.bar(
        x=list(driver_counts.keys()),
        y=list(driver_counts.values()),
        labels={'x': 'Driver Gene', 'y': 'Number of Patients'},
        color=list(driver_counts.keys()),
        title="Frequency of Key Driver Alterations",
        color_discrete_sequence=px.colors.qualitative.Bold
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # Pie chart showing distribution of LUAD vs LUSC
    st.subheader("Distribution of Lung Cancer Types")
    
    # Count LUAD vs LUSC
    cancer_type_counts = {
        'Lung Adenocarcinoma': sum('Lung Adenocarcinoma' in str(origin) for origin in patient_data['study_of_origin']),
        'Lung Squamous Cell Carcinoma': sum('Lung Squamous Cell Carcinoma' in str(origin) for origin in patient_data['study_of_origin'])
    }
    
    fig = px.pie(
        values=list(cancer_type_counts.values()),
        names=list(cancer_type_counts.keys()),
        title="Distribution of Lung Cancer Types",
        color_discrete_sequence=px.colors.qualitative.Safe
    )
    fig.update_traces(textinfo='percent+label')
    st.plotly_chart(fig, use_container_width=True)
"""
New patient tab functionality for the Precision Oncology application
"""

import streamlit as st
from config import app_config
from utils.data_processor import process_new_patient_data
from utils.therapy_recommender import get_therapy_recommendations
from utils.ai_integration import get_llm_recommendation
from modules.breast_cancer import get_breast_patient_considerations
from modules.lung_cancer import get_lung_patient_considerations

def render_new_patient(knowledge_base, openai_client, cancer_type):
    """
    Render the New Patient tab

    Args:
        knowledge_base: Dictionary with therapy knowledge base
        openai_client: AzureOpenAI client or None
        cancer_type: Type of cancer ("Breast Cancer" or "Lung Cancer")
    """
    st.header("New Patient Analysis")
    st.markdown("""
    Enter genomic data for a new patient to receive personalized therapy recommendations.
    This is useful for patients not already in the TCGA database or for planning potential therapies.
    """)
    
    if cancer_type == "Breast Cancer":
        render_breast_cancer_new_patient(knowledge_base, openai_client)
    else:  # Lung Cancer
        render_lung_cancer_new_patient(knowledge_base, openai_client)

def render_breast_cancer_new_patient(knowledge_base, openai_client):
    """
    Render the breast cancer specific new patient form

    Args:
        knowledge_base: Dictionary with therapy knowledge base
        openai_client: AzureOpenAI client or None
    """
    # Get the list of key genes to include in the form
    key_genes = app_config.BREAST_CANCER_KEY_GENES
    
    # Create form for entering new patient data
    with st.form("new_breast_patient_form"):
        st.subheader("Enter Patient Genomic Profile")
        
        # Patient identifier
        patient_name = st.text_input("Patient Identifier (optional):")
        
        # Create tabs for different alteration types
        gene_tabs = st.tabs(["Amplifications/Deletions", "Mutations", "Gene Expression"])
        
        # Tab 1: Amplifications/Deletions
        with gene_tabs[0]:
            st.markdown("**Select gene amplifications and deletions:**")
            
            for gene in key_genes:
                col1, col2 = st.columns(2)
                with col1:
                    st.checkbox(f"{gene} Amplification", key=f"amp_{gene}")
                with col2:
                    st.checkbox(f"{gene} Deletion", key=f"del_{gene}")
        
        # Tab 2: Mutations
        with gene_tabs[1]:
            st.markdown("**Select gene mutations:**")
            
            for gene in key_genes:
                col1, col2 = st.columns(2)
                with col1:
                    has_mutation = st.checkbox(f"{gene} Mutation", key=f"mut_{gene}")
                with col2:
                    if has_mutation:
                        st.selectbox(
                            f"{gene} Mutation Type", 
                            ["Missense Mutation", "Truncating mutation", "Inframe Mutation", "splice"],
                            key=f"mut_type_{gene}"
                        )
        
        # Tab 3: Gene Expression
        with gene_tabs[2]:
            st.markdown("**Select gene expression levels:**")
            
            for gene in key_genes:
                st.selectbox(
                    f"{gene} Expression", 
                    ["Normal", "High", "Low"],
                    key=f"exp_{gene}"
                )
        
        # Submit button
        submit_button = st.form_submit_button("Generate Recommendations")
    
    # Process the form data when submitted
    if submit_button:
        # Get all form data
        form_data = st.session_state
        
        # Process the patient data
        new_patient = process_new_patient_data(form_data, key_genes, "Breast Cancer")
        
        # Store the processed patient in session state for later use
        st.session_state['breast_new_patient_data'] = new_patient
        
        st.subheader("Analysis Results")
        
        # Display patient profile
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.markdown("**Patient Profile**")
            if patient_name:
                st.write(f"**Patient ID:** {patient_name}")
            st.write(f"**Breast Cancer Subtype:** {new_patient['breast_cancer_subtype']}")
            st.write(f"**Optimal Therapy Level:** {new_patient['optimal_therapy_level']}")
            
            st.markdown("**Genomic Alterations**")
            
            # Display gene amplifications
            if len(new_patient['gene_amplifications']) > 0:
                st.write("**Amplifications:**")
                for gene in new_patient['gene_amplifications']:
                    st.write(f"- {gene}")
            
            # Display gene deletions
            if len(new_patient['gene_deletions']) > 0:
                st.write("**Deletions:**")
                for gene in new_patient['gene_deletions']:
                    st.write(f"- {gene}")
            
            # Display gene mutations
            if len(new_patient['gene_mutations']) > 0:
                st.write("**Mutations:**")
                for mutation in new_patient['gene_mutations']:
                    st.write(f"- {mutation}")
            
            # Display highly expressed genes
            if 'high_expression' in new_patient and len(new_patient['high_expression']) > 0:
                st.write("**High Expression:**")
                for gene in new_patient['high_expression']:
                    st.write(f"- {gene}")
            
            # Display lowly expressed genes
            if 'low_expression' in new_patient and len(new_patient['low_expression']) > 0:
                st.write("**Low Expression:**")
                for gene in new_patient['low_expression']:
                    st.write(f"- {gene}")
        
        with col2:
            # Get therapy recommendations
            base_recommendations, special_recommendations = get_therapy_recommendations(
                new_patient, knowledge_base, "Breast Cancer"
            )
            
            st.subheader("Therapy Recommendations")
            
            # Display the therapy level description
            therapy_level = new_patient['optimal_therapy_level']
            level_str = str(therapy_level)
            therapy_level_info = knowledge_base["therapy_levels"][level_str]
            
            st.markdown(f"### {therapy_level_info['name']}")
            st.markdown(f"*{therapy_level_info['description']}*")
            
            # Display standard recommendations for this subtype and level
            st.markdown("#### Standard Approach:")
            if base_recommendations:
                for therapy, details in base_recommendations:
                    st.markdown(f"* **{therapy}**: {details}")
            else:
                st.info("No standard recommendations available for this specific patient profile.")
            
            # Display special recommendations based on genomic alterations
            if special_recommendations:
                st.markdown("#### Targeted Approaches:")
                for therapy, reason in special_recommendations:
                    st.markdown(f"* **{therapy}**: {reason}")
            
            # Display clinical considerations
            st.markdown("#### Clinical Considerations:")
            
            # Get clinical considerations
            considerations = get_breast_patient_considerations(new_patient)
            
            # Display the considerations
            for consideration in considerations:
                st.markdown(f"* {consideration}")
            
            # Display follow-up recommendations
            st.markdown("#### Follow-up Recommendations:")
            st.markdown(f"* {therapy_level_info['follow_up']}")
            st.markdown(f"* {therapy_level_info['monitoring']}")
            
            # Display a stylized therapy level gauge
            st.markdown("---")
            st.markdown("### Therapy Intensity")
            
            # Create a progress bar to visualize therapy level
            st.progress(therapy_level/4)
            
            # Use emojis to indicate therapy intensity
            therapy_gauge = {
                1: "🟢 Low intensity therapy - Less aggressive approach",
                2: "🟡 Standard therapy - Balanced approach",
                3: "🟠 Intensified therapy - More aggressive approach",
                4: "🔴 Maximum intensity therapy - Most aggressive approach"
            }
            
            st.markdown(therapy_gauge[therapy_level])
    
    # AI-assisted recommendation section - OUTSIDE the submit_button block
    if openai_client and 'breast_new_patient_data' in st.session_state:
        st.markdown("---")
        st.subheader("AI-Assisted Recommendation")
        
        gen_ai_button = st.button("Generate AI Recommendation for New Patient")
        if gen_ai_button:
            with st.spinner("Generating AI recommendation..."):
                ai_recommendation = get_llm_recommendation(
                    st.session_state['breast_new_patient_data'], 
                    knowledge_base, 
                    openai_client,
                    "Breast Cancer"
                )
                st.markdown(ai_recommendation)

def render_lung_cancer_new_patient(knowledge_base, openai_client):
    """
    Render the lung cancer specific new patient form

    Args:
        knowledge_base: Dictionary with therapy knowledge base
        openai_client: AzureOpenAI client or None
    """
    # Get the list of key genes to include in the form
    key_genes = app_config.LUNG_CANCER_KEY_GENES
    
    # Create form for entering new patient data
    with st.form("new_lung_patient_form"):
        st.subheader("Enter Patient Genomic Profile")
        
        # Basic information
        col1, col2 = st.columns(2)
        with col1:
            patient_name = st.text_input("Patient Identifier (optional):")
        with col2:
            cancer_type = st.selectbox(
                "Cancer Type:",
                options=["Lung Adenocarcinoma (LUAD)", "Lung Squamous Cell Carcinoma (LUSC)"],
                index=0
            )
        
        # Create tabs for different alteration types
        gene_tabs = st.tabs(["Amplifications/Deletions", "Mutations", "Structural Variants"])
        
        # Tab 1: Amplifications/Deletions
        with gene_tabs[0]:
            st.markdown("**Select gene amplifications and deletions:**")
            
            for gene in key_genes:
                col1, col2 = st.columns(2)
                with col1:
                    st.checkbox(f"{gene} Amplification", key=f"amp_{gene}")
                with col2:
                    st.checkbox(f"{gene} Deletion", key=f"del_{gene}")
        
        # Tab 2: Mutations
        with gene_tabs[1]:
            st.markdown("**Select gene mutations:**")
            
            for gene in key_genes:
                col1, col2 = st.columns(2)
                with col1:
                    has_mutation = st.checkbox(f"{gene} Mutation", key=f"mut_{gene}")
                with col2:
                    if has_mutation:
                        st.selectbox(
                            f"{gene} Mutation Type", 
                            ["Missense Mutation (putative driver)", "Truncating mutation (putative driver)", 
                             "Inframe Mutation (putative driver)", "splice", "Missense Mutation (putative passenger)"],
                            key=f"mut_type_{gene}"
                        )
        
        # Tab 3: Structural Variants
        with gene_tabs[2]:
            st.markdown("**Select structural variants:**")
            
            for gene in key_genes:
                col1, col2 = st.columns(2)
                with col1:
                    has_sv = st.checkbox(f"{gene} Structural Variant", key=f"sv_{gene}")
                with col2:
                    if has_sv:
                        st.selectbox(
                            f"{gene} Variant Type", 
                            ["sv", "sv_rec", "fusion", "rearrangement"],
                            key=f"sv_type_{gene}"
                        )
        
        # Submit button
        submit_button = st.form_submit_button("Generate Recommendations")
    
    # Process the form data when submitted
    if submit_button:
        # Get all form data
        form_data = st.session_state
        form_data['cancer_type'] = cancer_type
        
        # Process the patient data
        new_patient = process_new_patient_data(form_data, key_genes, "Lung Cancer")
        
        # Store the processed patient in session state for later use
        st.session_state['lung_new_patient_data'] = new_patient
        
        st.subheader("Analysis Results")
        
        # Display patient profile
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.markdown("**Patient Profile**")
            if patient_name:
                st.write(f"**Patient ID:** {patient_name}")
            st.write(f"**Cancer Type:** {new_patient['study_of_origin']}")
            st.write(f"**Molecular Subtype:** {new_patient['lung_cancer_subtype']}")
            st.write(f"**Optimal Therapy Level:** {new_patient['optimal_therapy_level']}")
            
            st.markdown("**Genomic Alterations**")
            
            # Display gene amplifications
            if len(new_patient['gene_amplifications']) > 0:
                st.write("**Amplifications:**")
                for gene in new_patient['gene_amplifications']:
                    st.write(f"- {gene}")
            
            # Display gene deletions
            if len(new_patient['gene_deletions']) > 0:
                st.write("**Deletions:**")
                for gene in new_patient['gene_deletions']:
                    st.write(f"- {gene}")
            
            # Display gene mutations
            if len(new_patient['gene_mutations']) > 0:
                st.write("**Mutations:**")
                for mutation in new_patient['gene_mutations']:
                    st.write(f"- {mutation}")
            
            # Display structural variants
            if 'structural_variants' in new_patient and len(new_patient['structural_variants']) > 0:
                st.write("**Structural Variants:**")
                for sv in new_patient['structural_variants']:
                    st.write(f"- {sv}")
        
        with col2:
            # Get therapy recommendations
            base_recommendations, special_recommendations = get_therapy_recommendations(
                new_patient, knowledge_base, "Lung Cancer"
            )
            
            st.subheader("Therapy Recommendations")
            
            # Display the therapy level description
            therapy_level = new_patient['optimal_therapy_level']
            level_str = str(therapy_level)
            therapy_level_info = knowledge_base["therapy_levels"][level_str]
            
            st.markdown(f"### {therapy_level_info['name']}")
            st.markdown(f"*{therapy_level_info['description']}*")
            
            # Display standard recommendations for this subtype and level
            st.markdown("#### Standard Approach:")
            if base_recommendations:
                for therapy, details in base_recommendations:
                    st.markdown(f"* **{therapy}**: {details}")
            else:
                st.info("No standard recommendations available for this specific patient profile.")
            
            # Display special recommendations based on genomic alterations
            if special_recommendations:
                st.markdown("#### Targeted Approaches:")
                for therapy, reason in special_recommendations:
                    st.markdown(f"* **{therapy}**: {reason}")
            
            # Display clinical considerations
            st.markdown("#### Clinical Considerations:")
            
            # Get clinical considerations
            considerations = get_lung_patient_considerations(new_patient)
            
            # Display the considerations
            for consideration in considerations:
                st.markdown(f"* {consideration}")
            
            # Display follow-up recommendations
            st.markdown("#### Follow-up Recommendations:")
            st.markdown(f"* {therapy_level_info['follow_up']}")
            st.markdown(f"* {therapy_level_info['monitoring']}")
            
            # Display a stylized therapy level gauge
            st.markdown("---")
            st.markdown("### Therapy Intensity")
            
            # Create a progress bar to visualize therapy level
            st.progress(therapy_level/4)
            
            # Use emojis to indicate therapy intensity
            therapy_gauge = {
                1: "🟢 Low intensity therapy - Less aggressive approach",
                2: "🟡 Standard therapy - Balanced approach",
                3: "🟠 Intensified therapy - More aggressive approach",
                4: "🔴 Maximum intensity therapy - Most aggressive approach"
            }
            
            st.markdown(therapy_gauge[therapy_level])
    
    # AI-assisted recommendation section - OUTSIDE the submit_button block
    if openai_client and 'lung_new_patient_data' in st.session_state:
        st.markdown("---")
        st.subheader("AI-Assisted Recommendation")
        
        gen_ai_button = st.button("Generate AI Recommendation for New Patient")
        if gen_ai_button:
            with st.spinner("Generating AI recommendation..."):
                ai_recommendation = get_llm_recommendation(
                    st.session_state['lung_new_patient_data'], 
                    knowledge_base, 
                    openai_client,
                    "Lung Cancer"
                )
                st.markdown(ai_recommendation)
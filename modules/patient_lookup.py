"""
Patient lookup tab functionality for the Precision Oncology application
"""

import streamlit as st
from utils.therapy_recommender import get_therapy_recommendations
from utils.ai_integration import get_llm_recommendation
from modules.breast_cancer import get_breast_patient_considerations
from modules.lung_cancer import get_lung_patient_considerations

def render_patient_lookup(patient_data, knowledge_base, openai_client, cancer_type):
    """
    Render the Patient Lookup tab

    Args:
        patient_data: DataFrame with patient data
        knowledge_base: Dictionary with therapy knowledge base
        openai_client: AzureOpenAI client or None
        cancer_type: Type of cancer ("Breast Cancer" or "Lung Cancer")
    """
    st.header("Patient Therapy Recommendation")
    
    # Patient selection - example IDs based on cancer type
    if cancer_type == "Breast Cancer":
        example_id = "TCGA-BH-A0C0"
        placeholder_text = "Enter Patient ID (e.g., TCGA-BH-A0C0):"
    else:  # Lung Cancer
        example_id = "TCGA-05-4384"
        placeholder_text = "Enter Patient ID (e.g., TCGA-05-4384):"
    
    patient_id_input = st.text_input(placeholder_text)
    
    if patient_id_input:
        # Make sure the patient ID is valid
        if patient_id_input in patient_data.index:
            # Get the patient's data
            selected_patient = patient_data.loc[patient_id_input]
            
            # Create two columns for display
            col1, col2 = st.columns([1, 2])
            
            with col1:
                st.subheader("Patient Profile")
                st.write(f"**Patient ID:** {patient_id_input}")
                
                if cancer_type == "Breast Cancer":
                    st.write(f"**Breast Cancer Subtype:** {selected_patient['breast_cancer_subtype']}")
                else:  # Lung Cancer
                    st.write(f"**Cancer Type:** {selected_patient['study_of_origin']}")
                    st.write(f"**Molecular Subtype:** {selected_patient['lung_cancer_subtype']}")
                
                st.write(f"**Optimal Therapy Level:** {selected_patient['optimal_therapy_level']}")
                
                st.subheader("Genomic Alterations")
                
                # Display gene amplifications
                if len(selected_patient['gene_amplifications']) > 0:
                    st.write("**Amplifications:**")
                    for gene in selected_patient['gene_amplifications']:
                        st.write(f"- {gene}")
                
                # Display gene deletions
                if len(selected_patient['gene_deletions']) > 0:
                    st.write("**Deletions:**")
                    for gene in selected_patient['gene_deletions']:
                        st.write(f"- {gene}")
                
                # Display gene mutations
                if len(selected_patient['gene_mutations']) > 0:
                    st.write("**Mutations:**")
                    for mutation in selected_patient['gene_mutations']:
                        st.write(f"- {mutation}")
                
                # Display cancer-specific alterations
                if cancer_type == "Breast Cancer":
                    # Display highly expressed genes
                    if 'high_expression' in selected_patient and len(selected_patient['high_expression']) > 0:
                        st.write("**High Expression:**")
                        for gene in selected_patient['high_expression']:
                            st.write(f"- {gene}")
                    
                    # Display lowly expressed genes
                    if 'low_expression' in selected_patient and len(selected_patient['low_expression']) > 0:
                        st.write("**Low Expression:**")
                        for gene in selected_patient['low_expression']:
                            st.write(f"- {gene}")
                else:  # Lung Cancer
                    # Display structural variants
                    if 'structural_variants' in selected_patient and len(selected_patient['structural_variants']) > 0:
                        st.write("**Structural Variants:**")
                        for sv in selected_patient['structural_variants']:
                            st.write(f"- {sv}")
            
            with col2:
                # Get therapy recommendations
                base_recommendations, special_recommendations = get_therapy_recommendations(
                    selected_patient, knowledge_base, cancer_type
                )
                
                st.subheader("Therapy Recommendations")
                
                # Get the subtype key based on cancer type
                subtype_key = 'breast_cancer_subtype' if cancer_type == "Breast Cancer" else 'lung_cancer_subtype'
                
                # Display the therapy level description
                therapy_level = selected_patient['optimal_therapy_level']
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
                
                # Get clinical considerations based on cancer type
                if cancer_type == "Breast Cancer":
                    considerations = get_breast_patient_considerations(selected_patient)
                else:  # Lung Cancer
                    considerations = get_lung_patient_considerations(selected_patient)
                
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
                
                # AI-assisted recommendation
                if openai_client:
                    st.markdown("---")
                    st.subheader("AI-Assisted Recommendation")
                    
                    if st.button("Generate AI Recommendation"):
                        with st.spinner("Generating AI recommendation..."):
                            ai_recommendation = get_llm_recommendation(
                                selected_patient, knowledge_base, openai_client, cancer_type
                            )
                            st.markdown(ai_recommendation)
        else:
            st.error(f"Patient ID '{patient_id_input}' not found in the database.")
            st.write("Please enter a valid patient ID from the TCGA dataset.")
            
            # Show a few available IDs as examples
            st.subheader("Sample available patient IDs:")
            st.write(", ".join(list(patient_data.index)[:10]))
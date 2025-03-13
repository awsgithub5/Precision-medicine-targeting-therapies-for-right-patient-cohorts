"""
Azure OpenAI integration for AI-assisted treatment recommendations
"""

import os
import streamlit as st
from openai import AzureOpenAI
from config import app_config

def initialize_azure_openai():
    """
    Initialize the Azure OpenAI client

    Returns:
        AzureOpenAI client or None if not configured
    """
    # Get environment variables or use placeholders - set these in your deployment environment
    # You can also add these to Streamlit secrets if running locally
    api_key = os.getenv("AZURE_OPENAI_API_KEY", st.secrets.get("AZURE_OPENAI_API_KEY", ""))
    endpoint = os.getenv("AZURE_OPENAI_ENDPOINT", st.secrets.get("AZURE_OPENAI_ENDPOINT", ""))
    
    if not api_key or not endpoint:
        st.warning("Azure OpenAI credentials not configured. AI-assisted recommendations will not be available.")
        return None
    
    try:
        client = AzureOpenAI(
            api_key=api_key,
            api_version=app_config.AZURE_OPENAI_API_VERSION,
            azure_endpoint=endpoint
        )
        return client
    except Exception as e:
        st.error(f"Failed to initialize Azure OpenAI client: {e}")
        return None

def get_llm_recommendation(patient_profile, knowledge_base, client, cancer_type):
    """
    Use Azure OpenAI to generate therapy recommendations for a patient
    
    Args:
        patient_profile: Dictionary with patient's molecular profile
        knowledge_base: Dictionary with therapy knowledge base
        client: AzureOpenAI client
        cancer_type: Type of cancer ("Breast Cancer" or "Lung Cancer")
    
    Returns:
        string: AI-generated recommendation
    """
    if client is None:
        return "AI recommendation not available (Azure OpenAI not configured)"
    
    # Determine which profile keys to use based on the cancer type
    if cancer_type == "Breast Cancer":
        subtype_key = 'breast_cancer_subtype'
        profile_text = f"""
        Patient Profile:
        - Breast Cancer Subtype: {patient_profile[subtype_key]}
        - Genomic Alterations:
            - Amplifications: {', '.join(patient_profile['gene_amplifications']) if len(patient_profile['gene_amplifications']) > 0 else 'None'}
            - Deletions: {', '.join(patient_profile['gene_deletions']) if len(patient_profile['gene_deletions']) > 0 else 'None'}
            - Mutations: {', '.join(patient_profile['gene_mutations']) if len(patient_profile['gene_mutations']) > 0 else 'None'}
            - High Expression: {', '.join(patient_profile['high_expression']) if 'high_expression' in patient_profile and len(patient_profile['high_expression']) > 0 else 'None'}
            - Low Expression: {', '.join(patient_profile['low_expression']) if 'low_expression' in patient_profile and len(patient_profile['low_expression']) > 0 else 'None'}
        """
        
        prompt = f"""
        You are an expert oncologist specializing in precision medicine for breast cancer. 
        You need to provide a therapy recommendation for a patient based on their molecular profile.
        
        {profile_text}
        
        Based on this profile and your knowledge of breast cancer therapeutics, please:
        1. Suggest an optimal therapy level (1-4, where 1 is low intensity and 4 is maximum intensity)
        2. Recommend specific therapies appropriate for this patient's molecular profile
        3. Note any special considerations based on specific genomic alterations
        4. Suggest appropriate follow-up and monitoring
        
        Consider these important factors in your recommendation:
        - TP53 mutations suggest more aggressive disease and may require more intensive therapy
        - BRCA1/2 mutations indicate potential benefit from PARP inhibitors and platinum chemotherapy
        - PIK3CA mutations in ER+ disease may benefit from PI3K inhibitors
        - ERBB2 (HER2) amplification indicates need for HER2-targeted therapy
        - MYC or CCND1 amplifications suggest genomic instability and may require more intensive approach
        - PTEN or RB1 loss may impact therapy response
        
        Provide your recommendation in a concise, structured format. Only include therapies that are supported by evidence and appropriate for this specific molecular profile.
        """
    else:  # Lung Cancer
        subtype_key = 'lung_cancer_subtype'
        profile_text = f"""
        Patient Profile:
        - Lung Cancer Subtype: {patient_profile[subtype_key]}
        - Genomic Alterations:
            - Amplifications: {', '.join(patient_profile['gene_amplifications']) if len(patient_profile['gene_amplifications']) > 0 else 'None'}
            - Deletions: {', '.join(patient_profile['gene_deletions']) if len(patient_profile['gene_deletions']) > 0 else 'None'}
            - Mutations: {', '.join(patient_profile['gene_mutations']) if len(patient_profile['gene_mutations']) > 0 else 'None'}
            - Structural Variants: {', '.join(patient_profile['structural_variants']) if 'structural_variants' in patient_profile and len(patient_profile['structural_variants']) > 0 else 'None'}
        """

        prompt = f"""
        You are an expert oncologist specializing in precision medicine for lung cancer. 
        You need to provide a therapy recommendation for a patient based on their molecular profile.
        
        {profile_text}
        
        Based on this profile and your knowledge of lung cancer therapeutics, please:
        1. Suggest an optimal therapy level (1-4, where 1 is low intensity and 4 is maximum intensity)
        2. Recommend specific therapies appropriate for this patient's molecular profile
        3. Note any special considerations based on specific genomic alterations
        4. Suggest appropriate follow-up and monitoring
        
        Consider these important factors in your recommendation:
        - EGFR mutations are key drivers in lung adenocarcinoma and indicate use of EGFR TKIs like Osimertinib
        - ALK rearrangements indicate use of ALK TKIs like Alectinib
        - ROS1 rearrangements suggest use of ROS1 TKIs like Entrectinib
        - KRAS G12C mutations can be targeted with Sotorasib or Adagrasib
        - TP53 mutations suggest more genomic instability and may require more intensive approach
        
        Provide your recommendation in a concise, structured format. Only include therapies that are supported by evidence and appropriate for this specific molecular profile.
        """
    
    try:
        response = client.chat.completions.create(
            model=os.getenv("AZURE_OPENAI_DEPLOYMENT", st.secrets.get("AZURE_OPENAI_DEPLOYMENT", app_config.AZURE_OPENAI_DEPLOYMENT)),
            messages=[
                {"role": "system", "content": f"You are an AI oncology assistant specializing in precision medicine for {cancer_type.lower()}."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=app_config.AZURE_OPENAI_MAX_TOKENS,
            temperature=app_config.AZURE_OPENAI_TEMPERATURE
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error generating AI recommendation: {str(e)}"
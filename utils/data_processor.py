"""
Functions for processing patient data
"""

import pandas as pd
from modules.breast_cancer import classify_breast_cancer_subtype, determine_breast_therapy_level
from modules.lung_cancer import classify_lung_cancer_subtype, determine_lung_therapy_level

def process_breast_cancer_data(tcga_data):
    """
    Process raw TCGA breast cancer data into a patient-centric dataframe

    Args:
        tcga_data: Raw dataframe from TSV file

    Returns:
        Tuple of (processed_dataframe, raw_dataframe)
    """
    # The first 2 columns contain metadata (track_name, track_type)
    # The remaining columns are patient IDs
    patient_ids = tcga_data.columns[2:]  # All columns except the first two
    genes = tcga_data['track_name'].unique()  # Get unique gene names
    
    # Create a patient-centric dictionary to store features
    patient_features = {}
    
    # Process each patient
    for patient_id in patient_ids:
        patient_features[patient_id] = {
            'gene_amplifications': [],
            'gene_deletions': [],
            'gene_mutations': [],
            'high_expression': [],
            'low_expression': []
        }
        
        # Process each gene for this patient
        for gene in genes:
            # Get CNA (Copy Number Alterations)
            cna_data = tcga_data[(tcga_data['track_name'] == gene) & (tcga_data['track_type'] == 'CNA')]
            if not cna_data.empty and pd.notna(cna_data.iloc[0][patient_id]):
                value = cna_data.iloc[0][patient_id]
                if 'amp' in str(value).lower():
                    patient_features[patient_id]['gene_amplifications'].append(gene)
                elif 'homdel' in str(value).lower() or 'deletion' in str(value).lower():
                    patient_features[patient_id]['gene_deletions'].append(gene)
            
            # Get Mutations
            mut_data = tcga_data[(tcga_data['track_name'] == gene) & (tcga_data['track_type'] == 'MUTATIONS')]
            if not mut_data.empty and pd.notna(mut_data.iloc[0][patient_id]):
                mutation_value = mut_data.iloc[0][patient_id]
                if mutation_value and str(mutation_value).lower() != 'nan':
                    patient_features[patient_id]['gene_mutations'].append(f"{gene}:{mutation_value}")
                
            # Get mRNA expression
            mrna_data = tcga_data[(tcga_data['track_name'] == gene) & (tcga_data['track_type'] == 'MRNA')]
            if not mrna_data.empty and pd.notna(mrna_data.iloc[0][patient_id]):
                expression = mrna_data.iloc[0][patient_id]
                if 'high' in str(expression).lower():
                    patient_features[patient_id]['high_expression'].append(gene)
                elif 'low' in str(expression).lower():
                    patient_features[patient_id]['low_expression'].append(gene)
    
    # Convert to DataFrame
    patients_df = pd.DataFrame.from_dict(patient_features, orient='index')
    
    # Add patient ID as a separate column
    patients_df['patient_id'] = patients_df.index
    
    # Add breast cancer subtype and therapy level
    patients_df['breast_cancer_subtype'] = patients_df.apply(classify_breast_cancer_subtype, axis=1)
    patients_df['optimal_therapy_level'] = patients_df.apply(determine_breast_therapy_level, axis=1)
    
    return patients_df, tcga_data

def process_lung_cancer_data(tcga_data):
    """
    Process raw TCGA lung cancer data into a patient-centric dataframe

    Args:
        tcga_data: Raw dataframe from TSV file

    Returns:
        Tuple of (processed_dataframe, raw_dataframe)
    """
    # The first 2 columns contain metadata (track_name, track_type)
    # The remaining columns are patient IDs
    patient_ids = tcga_data.columns[2:]  # All columns except the first two
    genes = tcga_data['track_name'].unique()  # Get unique gene names
    
    # Create a patient-centric dictionary to store features
    patient_features = {}
    
    # Process each patient
    for patient_id in patient_ids:
        patient_features[patient_id] = {
            'gene_amplifications': [],
            'gene_deletions': [],
            'gene_mutations': [],
            'structural_variants': [],
            'study_of_origin': None  # To store cancer type (LUAD or LUSC)
        }
        
        # Get the study of origin (cancer type)
        study_data = tcga_data[(tcga_data['track_name'] == 'Study of origin') & (tcga_data['track_type'] == 'CLINICAL')]
        if not study_data.empty and pd.notna(study_data.iloc[0][patient_id]):
            study = study_data.iloc[0][patient_id]
            patient_features[patient_id]['study_of_origin'] = study
        
        # Process each gene for this patient
        for gene in genes:
            # Skip Study of origin row
            if gene == 'Study of origin':
                continue
                
            # Get CNA (Copy Number Alterations)
            cna_data = tcga_data[(tcga_data['track_name'] == gene) & (tcga_data['track_type'] == 'CNA')]
            if not cna_data.empty and pd.notna(cna_data.iloc[0][patient_id]):
                value = cna_data.iloc[0][patient_id]
                if 'amp' in str(value).lower():
                    patient_features[patient_id]['gene_amplifications'].append(f"{gene}")
                elif 'deep deletion' in str(value).lower() or 'homdel' in str(value).lower():
                    patient_features[patient_id]['gene_deletions'].append(f"{gene}")
            
            # Get Mutations
            mut_data = tcga_data[(tcga_data['track_name'] == gene) & (tcga_data['track_type'] == 'MUTATIONS')]
            if not mut_data.empty and pd.notna(mut_data.iloc[0][patient_id]):
                mutation_value = mut_data.iloc[0][patient_id]
                if mutation_value and str(mutation_value).lower() != 'nan':
                    patient_features[patient_id]['gene_mutations'].append(f"{gene}:{mutation_value}")
                
            # Get structural variants
            sv_data = tcga_data[(tcga_data['track_name'] == gene) & (tcga_data['track_type'] == 'STRUCTURAL_VARIANT')]
            if not sv_data.empty and pd.notna(sv_data.iloc[0][patient_id]):
                sv_value = sv_data.iloc[0][patient_id]
                if sv_value and str(sv_value).lower() != 'nan':
                    patient_features[patient_id]['structural_variants'].append(f"{gene}:{sv_value}")
    
    # Convert to DataFrame
    patients_df = pd.DataFrame.from_dict(patient_features, orient='index')
    
    # Add patient ID as a separate column
    patients_df['patient_id'] = patients_df.index
    
    # Add lung cancer subtype and therapy level
    patients_df['lung_cancer_subtype'] = patients_df.apply(classify_lung_cancer_subtype, axis=1)
    patients_df['optimal_therapy_level'] = patients_df.apply(determine_lung_therapy_level, axis=1)
    
    return patients_df, tcga_data

def process_new_patient_data(form_data, genes_list, cancer_type):
    """
    Process manual input data for a new patient

    Args:
        form_data: Dictionary with form inputs
        genes_list: List of genes to process
        cancer_type: Type of cancer ("Breast Cancer" or "Lung Cancer")

    Returns:
        pandas.Series with processed patient data
    """
    if cancer_type == "Breast Cancer":
        patient_data = {
            'gene_amplifications': [],
            'gene_deletions': [],
            'gene_mutations': [],
            'high_expression': [],
            'low_expression': []
        }
        
        # Process gene amplifications
        for gene in genes_list:
            amp_key = f"amp_{gene}"
            del_key = f"del_{gene}"
            mut_key = f"mut_{gene}"
            exp_key = f"exp_{gene}"
            
            if amp_key in form_data and form_data[amp_key]:
                patient_data['gene_amplifications'].append(gene)
            
            if del_key in form_data and form_data[del_key]:
                patient_data['gene_deletions'].append(gene)
            
            if mut_key in form_data and form_data[mut_key]:
                mutation_type = form_data.get(f"mut_type_{gene}", "Mutation")
                patient_data['gene_mutations'].append(f"{gene}:{mutation_type}")
            
            if exp_key in form_data:
                if form_data[exp_key] == "High":
                    patient_data['high_expression'].append(gene)
                elif form_data[exp_key] == "Low":
                    patient_data['low_expression'].append(gene)
        
        # Convert to pandas Series for compatibility with existing functions
        patient_series = pd.Series(patient_data)
        
        # Determine breast cancer subtype and therapy level
        patient_series['breast_cancer_subtype'] = classify_breast_cancer_subtype(patient_series)
        patient_series['optimal_therapy_level'] = determine_breast_therapy_level(patient_series)
        
        return patient_series
    else:  # Lung Cancer
        patient_data = {
            'gene_amplifications': [],
            'gene_deletions': [],
            'gene_mutations': [],
            'structural_variants': [],
            'study_of_origin': form_data.get('cancer_type', 'Lung Adenocarcinoma (TCGA, PanCancer Atlas)')
        }
        
        # Process gene amplifications
        for gene in genes_list:
            amp_key = f"amp_{gene}"
            del_key = f"del_{gene}"
            mut_key = f"mut_{gene}"
            sv_key = f"sv_{gene}"
            
            if amp_key in form_data and form_data[amp_key]:
                patient_data['gene_amplifications'].append(gene)
            
            if del_key in form_data and form_data[del_key]:
                patient_data['gene_deletions'].append(gene)
            
            if mut_key in form_data and form_data[mut_key]:
                mutation_type = form_data.get(f"mut_type_{gene}", "Mutation")
                patient_data['gene_mutations'].append(f"{gene}:{mutation_type}")
            
            if sv_key in form_data and form_data[sv_key]:
                sv_type = form_data.get(f"sv_type_{gene}", "rearrangement")
                patient_data['structural_variants'].append(f"{gene}:{sv_type}")
        
        # Convert to pandas Series for compatibility with existing functions
        patient_series = pd.Series(patient_data)
        
        # Determine lung cancer subtype and therapy level
        patient_series['lung_cancer_subtype'] = classify_lung_cancer_subtype(patient_series)
        patient_series['optimal_therapy_level'] = determine_lung_therapy_level(patient_series)
        
        return patient_series
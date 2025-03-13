"""
Lung cancer specific functions for the Precision Oncology application
"""

import pandas as pd
from config import app_config

def classify_lung_cancer_subtype(row):
    """
    Determine lung cancer molecular subtype based on driver alterations

    Args:
        row: Dictionary or Series with patient's data

    Returns:
        string: Determined molecular subtype
    """
    # Check if we know the cancer type
    cancer_type = row['study_of_origin']
    if cancer_type is None:
        return "Unknown"
    
    # Extract LUAD or LUSC from the study of origin
    if 'Lung Adenocarcinoma' in str(cancer_type):
        base_type = 'LUAD'
    elif 'Lung Squamous Cell Carcinoma' in str(cancer_type):
        base_type = 'LUSC'
    else:
        base_type = "Unknown"
    
    # Check for known driver mutations
    has_egfr_alteration = any('EGFR' in m for m in row['gene_mutations']) or any('EGFR' in sv for sv in row['structural_variants']) if 'structural_variants' in row else False
    has_alk_alteration = any('ALK' in m for m in row['gene_mutations']) or any('ALK' in sv for sv in row['structural_variants']) if 'structural_variants' in row else False
    has_ros1_alteration = any('ROS1' in m for m in row['gene_mutations']) or any('ROS1' in sv for sv in row['structural_variants']) if 'structural_variants' in row else False
    has_kras_mutation = any('KRAS' in m for m in row['gene_mutations'])
    
    # Determine molecular subtype
    if base_type == 'LUAD':
        if has_egfr_alteration:
            return "LUAD EGFR-mutated"
        elif has_alk_alteration:
            return "LUAD ALK-rearranged"
        elif has_ros1_alteration:
            return "LUAD ROS1-rearranged"
        elif has_kras_mutation:
            return "LUAD KRAS-mutated"
        else:
            return "LUAD Other"
    elif base_type == 'LUSC':
        return "LUSC"
    else:
        return "Unknown"

def determine_lung_therapy_level(row):
    """
    Determine optimal therapy level (1-4) for lung cancer based on molecular profile

    Args:
        row: Dictionary or Series with patient's data

    Returns:
        int: Optimal therapy level (1-4)
    """
    # Start with intermediate therapy level
    base_level = 2
    
    # Adjust based on molecular subtype
    subtype = row['lung_cancer_subtype']
    if subtype == 'LUAD EGFR-mutated':
        # Check for specific mutations that indicate resistance
        has_resistance_mutation = any('T790M' in m for m in row['gene_mutations']) or any('C797S' in m for m in row['gene_mutations'])
        if has_resistance_mutation:
            base_level += 1  # More aggressive for TKI resistance mutations
    elif subtype == 'LUAD ALK-rearranged' or subtype == 'LUAD ROS1-rearranged':
        base_level += 0.5  # Moderate increase for rearrangements
    elif subtype == 'LUAD KRAS-mutated':
        # KRAS G12C is targetable, other KRAS mutations may need more aggressive approach
        has_g12c = any('G12C' in m for m in row['gene_mutations'])
        if not has_g12c:
            base_level += 0.5  # More aggressive for non-G12C KRAS
        
    # Adjust for TP53 mutations (associated with more aggressive disease)
    tp53_mutated = any('TP53' in mutation for mutation in row['gene_mutations'])
    if tp53_mutated:
        base_level += 0.5
    
    # Round to nearest therapy level (1-4)
    return max(1, min(4, round(base_level)))

def get_lung_cancer_recommendations(patient_data, knowledge_base):
    """
    Get specific therapy recommendations for lung cancer based on the patient's molecular profile

    Args:
        patient_data: Dictionary or Series with patient's molecular profile
        knowledge_base: Dictionary with therapy knowledge base

    Returns:
        Tuple of (base_recommendations, special_recommendations)
    """
    subtype = patient_data['lung_cancer_subtype']
    therapy_level = patient_data['optimal_therapy_level']
    level_str = str(therapy_level)
    
    recommendations = []
    special_recommendations = []
    
    # For EGFR-mutated LUAD
    if 'EGFR-mutated' in subtype:
        # First-line recommendations
        recommendations.append(("EGFR TKI Therapy", "Osimertinib preferred for first-line"))
        
        # Check for specific mutations
        has_exon20 = any('exon20' in str(m).lower() for m in patient_data['gene_mutations'])
        has_t790m = any('T790M' in str(m) for m in patient_data['gene_mutations'])
        
        if has_exon20:
            special_recommendations.append(("Amivantamab", "FDA-approved for EGFR exon20 insertion mutations"))
        
        if has_t790m:
            special_recommendations.append(("Osimertinib", "Effective against T790M resistance mutation"))
            
        if therapy_level >= 3:
            recommendations.append(("EGFR TKI + Anti-angiogenic", "Consider Osimertinib + Bevacizumab"))
        
        if therapy_level >= 4:
            recommendations.append(("Combination Therapy", "EGFR TKI + chemotherapy (platinum-pemetrexed)"))
            recommendations.append(("Clinical Trial", "Novel approaches for EGFR resistance"))
    
    # For ALK-rearranged LUAD
    elif 'ALK-rearranged' in subtype:
        recommendations.append(("ALK TKI Therapy", "Alectinib preferred for first-line"))
        
        if therapy_level >= 3:
            special_recommendations.append(("Lorlatinib", "For resistant disease or brain metastases"))
            
        if therapy_level >= 4:
            recommendations.append(("Combination Therapy", "Consider ALK TKI + chemotherapy"))
            recommendations.append(("Clinical Trial", "Novel approaches for ALK resistance"))
    
    # For ROS1-rearranged LUAD
    elif 'ROS1-rearranged' in subtype:
        recommendations.append(("ROS1 TKI Therapy", "Entrectinib (preferred if CNS disease) or Crizotinib"))
        
        if therapy_level >= 3:
            special_recommendations.append(("Lorlatinib or Repotrectinib", "For resistant disease"))
            
        if therapy_level >= 4:
            recommendations.append(("Clinical Trial", "Novel approaches for ROS1+ disease"))
    
    # For KRAS-mutated LUAD
    elif 'KRAS-mutated' in subtype:
        # Check for G12C mutation
        has_g12c = any('G12C' in str(m) for m in patient_data['gene_mutations'])
        
        if has_g12c:
            special_recommendations.append(("Sotorasib or Adagrasib", "FDA-approved for KRAS G12C mutation"))
        
        if therapy_level == 1:
            recommendations.append(("Immunotherapy", "Pembrolizumab for PD-L1 >50%"))
        elif therapy_level == 2:
            recommendations.append(("Chemo-Immunotherapy", "Platinum doublet + Pembrolizumab"))
        elif therapy_level >= 3:
            recommendations.append(("Intensive Chemotherapy", "Platinum doublet + Pembrolizumab + Bevacizumab"))
        if therapy_level >= 4:
            recommendations.append(("Clinical Trial", "Novel KRAS inhibitors or combinations"))
    
    # For LUSC or other LUAD
    else:
        if therapy_level == 1:
            recommendations.append(("Immunotherapy", "Pembrolizumab for PD-L1 >50%"))
        elif therapy_level == 2:
            recommendations.append(("Chemo-Immunotherapy", "Platinum doublet + Pembrolizumab"))
        elif therapy_level >= 3:
            recommendations.append(("Intensive Chemotherapy", "Platinum doublet + Pembrolizumab + additional agent"))
        if therapy_level >= 4:
            recommendations.append(("Clinical Trial", "Novel approaches or combinations"))
            recommendations.append(("Docetaxel + Ramucirumab", "For refractory disease"))
            
    # Remove duplicates
    special_recommendations = list(set(special_recommendations))
    
    return recommendations, special_recommendations

def create_default_lung_knowledge_base():
    """
    Create a default knowledge base for lung cancer therapy

    Returns:
        dict: Default knowledge base for lung cancer
    """
    return {
        "subtypes": {
            "LUAD EGFR-mutated": {
                "description": "Lung adenocarcinoma with EGFR driver mutations",
                "therapy_levels": {
                    "1": {
                        "name": "Low Intensity Therapy",
                        "description": "Conservative approach for low-risk disease",
                        "recommendations": [
                            {
                                "therapy": "EGFR TKI monotherapy",
                                "details": "Osimertinib, Gefitinib, or Erlotinib"
                            }
                        ]
                    },
                    "2": {
                        "name": "Standard Therapy",
                        "description": "Balanced approach for intermediate-risk disease",
                        "recommendations": [
                            {
                                "therapy": "EGFR TKI therapy",
                                "details": "Osimertinib preferred for first-line"
                            }
                        ]
                    },
                    "3": {
                        "name": "Intensified Therapy",
                        "description": "More aggressive approach for high-risk disease",
                        "recommendations": [
                            {
                                "therapy": "EGFR TKI + Anti-angiogenic",
                                "details": "Osimertinib + Bevacizumab or Ramucirumab"
                            }
                        ]
                    },
                    "4": {
                        "name": "Maximum Intensity Therapy",
                        "description": "Most aggressive approach for very high-risk disease",
                        "recommendations": [
                            {
                                "therapy": "Combination therapy",
                                "details": "EGFR TKI + chemotherapy"
                            }
                        ]
                    }
                }
            },
            "LUAD ALK-rearranged": {
                "description": "Lung adenocarcinoma with ALK gene rearrangements",
                "therapy_levels": {
                    "1": {
                        "name": "Low Intensity Therapy",
                        "description": "Conservative approach",
                        "recommendations": [
                            {
                                "therapy": "ALK TKI monotherapy",
                                "details": "Alectinib preferred"
                            }
                        ]
                    },
                    "2": {
                        "name": "Standard Therapy",
                        "description": "Standard approach",
                        "recommendations": [
                            {
                                "therapy": "ALK TKI therapy",
                                "details": "Alectinib preferred for first-line"
                            }
                        ]
                    },
                    "3": {
                        "name": "Intensified Therapy",
                        "description": "For high-risk disease",
                        "recommendations": [
                            {
                                "therapy": "Next-generation ALK TKI",
                                "details": "Lorlatinib for resistant disease or CNS involvement"
                            }
                        ]
                    },
                    "4": {
                        "name": "Maximum Intensity Therapy",
                        "description": "For very high-risk disease",
                        "recommendations": [
                            {
                                "therapy": "Combination therapy",
                                "details": "ALK TKI + chemotherapy or immunotherapy"
                            }
                        ]
                    }
                }
            },
            "LUAD KRAS-mutated": {
                "description": "Lung adenocarcinoma with KRAS mutations",
                "therapy_levels": {
                    "1": {
                        "name": "Low Intensity Therapy",
                        "description": "For G12C mutation",
                        "recommendations": [
                            {
                                "therapy": "KRAS G12C inhibitor",
                                "details": "Sotorasib or Adagrasib"
                            }
                        ]
                    },
                    "2": {
                        "name": "Standard Therapy",
                        "description": "For most KRAS mutated cases",
                        "recommendations": [
                            {
                                "therapy": "Chemo-immunotherapy",
                                "details": "Platinum-based chemotherapy + Pembrolizumab"
                            }
                        ]
                    },
                    "3": {
                        "name": "Intensified Therapy",
                        "description": "More aggressive approach",
                        "recommendations": [
                            {
                                "therapy": "Intensive chemotherapy",
                                "details": "Platinum-based chemotherapy + Pembrolizumab + Bevacizumab"
                            }
                        ]
                    },
                    "4": {
                        "name": "Maximum Intensity Therapy",
                        "description": "For aggressive disease",
                        "recommendations": [
                            {
                                "therapy": "Clinical trial",
                                "details": "Novel KRAS inhibitors or combinations"
                            }
                        ]
                    }
                }
            },
            "LUSC": {
                "description": "Lung squamous cell carcinoma",
                "therapy_levels": {
                    "1": {
                        "name": "Low Intensity Therapy",
                        "description": "For early stage or frail patients",
                        "recommendations": [
                            {
                                "therapy": "Single-agent immunotherapy",
                                "details": "Pembrolizumab for PD-L1 ≥50%"
                            }
                        ]
                    },
                    "2": {
                        "name": "Standard Therapy",
                        "description": "Standard approach",
                        "recommendations": [
                            {
                                "therapy": "Chemo-immunotherapy",
                                "details": "Platinum-based chemotherapy + Pembrolizumab"
                            }
                        ]
                    },
                    "3": {
                        "name": "Intensified Therapy",
                        "description": "More aggressive approach",
                        "recommendations": [
                            {
                                "therapy": "Intensified chemotherapy",
                                "details": "Platinum-based chemotherapy + Pembrolizumab + additional agent"
                            }
                        ]
                    },
                    "4": {
                        "name": "Maximum Intensity Therapy",
                        "description": "For refractory disease",
                        "recommendations": [
                            {
                                "therapy": "Docetaxel + Ramucirumab",
                                "details": "For refractory disease"
                            }
                        ]
                    }
                }
            }
        },
        "special_biomarkers": {
            "EGFR_mutation": {
                "clinical_significance": "Driver mutation and therapeutic target in NSCLC",
                "therapy_options": [
                    {
                        "name": "Osimertinib",
                        "indication": "First-line for EGFR mut+ NSCLC, better for brain mets"
                    },
                    {
                        "name": "Gefitinib/Erlotinib",
                        "indication": "First-generation TKIs for EGFR mut+ NSCLC"
                    }
                ]
            },
            "ALK_rearrangement": {
                "clinical_significance": "Driver alteration in NSCLC",
                "therapy_options": [
                    {
                        "name": "Alectinib",
                        "indication": "First-line for ALK+ NSCLC"
                    },
                    {
                        "name": "Lorlatinib",
                        "indication": "For resistant disease"
                    }
                ]
            },
            "KRAS_G12C_mutation": {
                "clinical_significance": "Targetable KRAS mutation",
                "therapy_options": [
                    {
                        "name": "Sotorasib",
                        "indication": "FDA-approved for KRAS G12C+ NSCLC"
                    },
                    {
                        "name": "Adagrasib",
                        "indication": "FDA-approved for KRAS G12C+ NSCLC"
                    }
                ]
            }
        },
        "therapy_levels": {
            "1": {
                "name": "Low Intensity Therapy",
                "description": "Conservative approach for low-risk disease",
                "follow_up": "Every 3 months with imaging",
                "monitoring": "Low-dose CT scans, symptom monitoring"
            },
            "2": {
                "name": "Standard Therapy",
                "description": "Balanced approach for most patients",
                "follow_up": "Every 2-3 months with imaging",
                "monitoring": "Regular CT scans, possible molecular testing"
            },
            "3": {
                "name": "Intensified Therapy",
                "description": "More aggressive approach for high-risk disease",
                "follow_up": "Every 6-8 weeks with imaging",
                "monitoring": "Regular CT/MRI, molecular testing for resistance"
            },
            "4": {
                "name": "Maximum Intensity Therapy",
                "description": "Most aggressive approach for very high-risk disease",
                "follow_up": "Every 6 weeks with imaging",
                "monitoring": "Frequent CT/MRI, molecular testing, close symptom monitoring"
            }
        }
    }

def get_lung_patient_considerations(patient_data):
    """
    Get clinical considerations for a lung cancer patient based on their profile

    Args:
        patient_data: Dictionary or Series with patient's molecular profile

    Returns:
        list: List of clinical considerations as strings
    """
    considerations = []
    
    # Based on molecular subtype
    if "EGFR-mutated" in patient_data['lung_cancer_subtype']:
        considerations.append("Monitor for EGFR TKI resistance mutations (T790M, C797S)")
        considerations.append("Consider liquid biopsy at progression")
    
    if "ALK-rearranged" in patient_data['lung_cancer_subtype']:
        considerations.append("Monitor for CNS progression (ALK+ disease has high CNS tropism)")
        considerations.append("Consider tissue/liquid biopsy at progression to identify resistance mechanisms")
    
    if "KRAS-mutated" in patient_data['lung_cancer_subtype']:
        considerations.append("Test for G12C mutation specifically, as it's targetable")
    
    if patient_data['optimal_therapy_level'] >= 3:
        considerations.append("Consider clinical trial enrollment for novel approaches")
        considerations.append("More frequent monitoring recommended")
    
    # Specific considerations based on genomic alterations
    if any('TP53' in m for m in patient_data['gene_mutations']):
        considerations.append("TP53 mutation suggests higher genomic instability and potentially more aggressive disease")
    
    return considerations

def get_lung_cancer_key_alterations(patient_data):
    """
    Count important gene alterations in the patient dataset
    
    Args:
        patient_data: DataFrame with patient data

    Returns:
        dict: Dictionary with gene counts
    """
    driver_counts = {
        'EGFR': sum(1 for patient in patient_data.itertuples() if 
                   any('EGFR' in m for m in patient.gene_mutations) or 
                   any('EGFR' in sv for sv in patient.structural_variants)),
        'ALK': sum(1 for patient in patient_data.itertuples() if 
                  any('ALK' in m for m in patient.gene_mutations) or 
                  any('ALK' in sv for sv in patient.structural_variants)),
        'ROS1': sum(1 for patient in patient_data.itertuples() if 
                   any('ROS1' in m for m in patient.gene_mutations) or 
                   any('ROS1' in sv for sv in patient.structural_variants)),
        'KRAS': sum(1 for patient in patient_data.itertuples() if 
                   any('KRAS' in m for m in patient.gene_mutations)),
        'TP53': sum(1 for patient in patient_data.itertuples() if 
                   any('TP53' in m for m in patient.gene_mutations))
    }
    
    return driver_counts
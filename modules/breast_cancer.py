"""
Breast cancer specific functions for the Precision Oncology application
"""

import pandas as pd
from config import app_config

def classify_breast_cancer_subtype(row):
    """
    Determine breast cancer subtype based on receptor status

    Args:
        row: Dictionary or Series with patient's data

    Returns:
        string: Determined molecular subtype
    """
    # Check if HER2 is amplified or highly expressed
    her2_positive = ('ERBB2' in row['gene_amplifications'] or 
                    ('high_expression' in row and 'ERBB2' in row['high_expression']))
    
    # Check if ER is highly expressed or ESR1 is amplified
    er_positive = (('high_expression' in row and 'ESR1' in row['high_expression']) or 
                   'ESR1' in row['gene_amplifications'])
    
    # Classify based on receptor status
    if er_positive and not her2_positive:
        return "Luminal A/B"
    elif er_positive and her2_positive:
        return "Luminal HER2+"
    elif not er_positive and her2_positive:
        return "HER2 Enriched"
    else:  # ER-, HER2-
        return "Triple Negative"

def determine_breast_therapy_level(row):
    """
    Determine optimal therapy level (1-4) for breast cancer based on molecular profile

    Args:
        row: Dictionary or Series with patient's data

    Returns:
        int: Optimal therapy level (1-4)
    """
    # Start with intermediate therapy level
    base_level = 2
    
    # Adjust based on molecular subtype
    subtype = row['breast_cancer_subtype']
    if subtype == 'Triple Negative':
        base_level += 1  # More aggressive for TNBC
    elif subtype == 'HER2 Enriched':
        base_level += 0.5  # Moderate increase for HER2
    elif subtype == 'Luminal A/B':
        base_level -= 0.5  # Less aggressive for hormone positive
        
    # Adjust for TP53 mutations (associated with more aggressive disease)
    tp53_mutated = any('TP53' in mutation for mutation in row['gene_mutations'])
    if tp53_mutated:
        base_level += 0.5
        
    # Adjust for BRCA1/2 mutations (PARP inhibitor candidates)
    brca_mutated = any('BRCA1' in mutation or 'BRCA2' in mutation 
                      for mutation in row['gene_mutations'])
    if brca_mutated:
        base_level += 0.5
        
    # Adjust for genomic instability markers
    if 'MYC' in row['gene_amplifications'] or 'CCND1' in row['gene_amplifications']:
        base_level += 0.3
        
    # Adjust for tumor suppressor loss
    if 'PTEN' in row['gene_deletions'] or 'RB1' in row['gene_deletions']:
        base_level += 0.4
        
    # Round to nearest therapy level (1-4)
    return max(1, min(4, round(base_level)))

def get_breast_cancer_recommendations(patient_data, knowledge_base):
    """
    Get specific therapy recommendations for breast cancer based on the patient's molecular profile

    Args:
        patient_data: Dictionary or Series with patient's molecular profile
        knowledge_base: Dictionary with therapy knowledge base

    Returns:
        Tuple of (base_recommendations, special_recommendations)
    """
    subtype = patient_data['breast_cancer_subtype']
    therapy_level = patient_data['optimal_therapy_level']
    level_str = str(therapy_level)
    
    # Check if subtype exists in knowledge base
    if subtype not in knowledge_base["subtypes"]:
        return [], []
    
    # Check if therapy level exists for this subtype
    if level_str not in knowledge_base["subtypes"][subtype]["therapy_levels"]:
        return [], []
    
    # Get standard recommendations for this subtype and therapy level
    recommendations = []
    therapy_data = knowledge_base["subtypes"][subtype]["therapy_levels"][level_str]
    
    for rec in therapy_data["recommendations"]:
        recommendation = (rec["therapy"], rec.get("details", ""))
        recommendations.append(recommendation)
    
    # Get special recommendations based on biomarkers
    special_recommendations = []
    
    # Check for actionable mutations/alterations
    for mutation in patient_data['gene_mutations']:
        gene = mutation.split(':')[0]
        
        # Check if this gene has special recommendations in knowledge base
        biomarker_key = f"{gene}_mutation"
        if biomarker_key in knowledge_base["special_biomarkers"]:
            biomarker_data = knowledge_base["special_biomarkers"][biomarker_key]
            
            # Add therapy options if available
            if "therapy_options" in biomarker_data:
                for therapy in biomarker_data["therapy_options"]:
                    special_rec = (therapy["name"], therapy.get("indication", ""))
                    special_recommendations.append(special_rec)
    
    # Check for gene amplifications
    for gene in patient_data['gene_amplifications']:
        biomarker_key = f"{gene}_amplification"
        if biomarker_key in knowledge_base["special_biomarkers"]:
            biomarker_data = knowledge_base["special_biomarkers"][biomarker_key]
            
            # Add therapy options if available
            if "therapy_options" in biomarker_data:
                for therapy in biomarker_data["therapy_options"]:
                    special_rec = (therapy["name"], therapy.get("indication", ""))
                    special_recommendations.append(special_rec)
    
    # Check for gene deletions or loss
    for gene in patient_data['gene_deletions']:
        biomarker_key = f"{gene}_loss"
        if biomarker_key in knowledge_base["special_biomarkers"]:
            biomarker_data = knowledge_base["special_biomarkers"][biomarker_key]
            
            # Add therapy options if available
            if "therapy_options" in biomarker_data:
                for therapy in biomarker_data["therapy_options"]:
                    special_rec = (therapy["name"], therapy.get("indication", ""))
                    special_recommendations.append(special_rec)
    
    # Remove duplicates
    special_recommendations = list(set(special_recommendations))
    
    return recommendations, special_recommendations

def get_breast_patient_considerations(patient_data):
    """
    Get clinical considerations for a breast cancer patient based on their profile

    Args:
        patient_data: Dictionary or Series with patient's molecular profile

    Returns:
        list: List of clinical considerations as strings
    """
    considerations = []
    
    therapy_level = patient_data['optimal_therapy_level']
    
    if therapy_level >= 3:
        considerations.append("Consider clinical trial enrollment for novel approaches")
        considerations.append("More frequent monitoring (every 2-3 months)")
    
    # Specific considerations based on genomic alterations
    if any('TP53' in m for m in patient_data['gene_mutations']):
        considerations.append("TP53 mutation suggests higher risk of recurrence")
    
    if any('BRCA' in m for m in patient_data['gene_mutations']):
        considerations.append("Consider genetic counseling for hereditary cancer risk")
    
    if 'ERBB2' in patient_data['gene_amplifications']:
        considerations.append("HER2-targeted therapy is essential component of treatment")
    
    if 'high_expression' in patient_data and 'ESR1' in patient_data['high_expression'] and therapy_level >= 2:
        considerations.append("Extended endocrine therapy may be beneficial (5-10 years)")
    
    return considerations

def create_default_breast_knowledge_base():
    """
    Create a default knowledge base for breast cancer therapy

    Returns:
        dict: Default knowledge base for breast cancer
    """
    return {
        "subtypes": {
            "Luminal A/B": {
                "description": "Hormone receptor positive, HER2 negative breast cancer",
                "therapy_levels": {
                    "1": {
                        "name": "Low Intensity Therapy",
                        "description": "Conservative approach for low-risk disease",
                        "recommendations": [
                            {
                                "therapy": "Endocrine therapy alone",
                                "details": "Tamoxifen or Aromatase Inhibitor"
                            }
                        ]
                    },
                    "2": {
                        "name": "Standard Therapy",
                        "description": "Balanced approach for intermediate-risk disease",
                        "recommendations": [
                            {
                                "therapy": "Endocrine therapy",
                                "details": "Tamoxifen or Aromatase Inhibitor +/- Ovarian Suppression"
                            },
                            {
                                "therapy": "Consider chemotherapy",
                                "details": "Based on genomic assays (OncotypeDx, MammaPrint)"
                            }
                        ]
                    },
                    "3": {
                        "name": "Intensified Therapy",
                        "description": "More aggressive approach for high-risk disease",
                        "recommendations": [
                            {
                                "therapy": "Chemotherapy",
                                "details": "Anthracycline and/or taxane-based regimen"
                            },
                            {
                                "therapy": "Followed by endocrine therapy",
                                "details": "Extended duration (5-10 years)"
                            }
                        ]
                    },
                    "4": {
                        "name": "Maximum Intensity Therapy",
                        "description": "Most aggressive approach for very high-risk disease",
                        "recommendations": [
                            {
                                "therapy": "Dose-dense chemotherapy",
                                "details": "AC-T or TAC regimen"
                            },
                            {
                                "therapy": "Consider CDK4/6 inhibitor",
                                "details": "With endocrine therapy in high-risk cases"
                            }
                        ]
                    }
                }
            },
            "Luminal HER2+": {
                "description": "Hormone receptor positive, HER2 positive breast cancer",
                "therapy_levels": {
                    "1": {
                        "name": "Low Intensity Therapy",
                        "description": "For very small, node-negative tumors",
                        "recommendations": [
                            {
                                "therapy": "HER2-targeted therapy",
                                "details": "Trastuzumab +/- Pertuzumab"
                            },
                            {
                                "therapy": "Endocrine therapy",
                                "details": "Tamoxifen or Aromatase Inhibitor"
                            }
                        ]
                    },
                    "2": {
                        "name": "Standard Therapy",
                        "description": "Standard approach for most patients",
                        "recommendations": [
                            {
                                "therapy": "Chemotherapy + HER2-targeted therapy",
                                "details": "Taxane-based chemotherapy with Trastuzumab + Pertuzumab"
                            },
                            {
                                "therapy": "Followed by endocrine therapy",
                                "details": "For 5-10 years"
                            }
                        ]
                    },
                    "3": {
                        "name": "Intensified Therapy",
                        "description": "For higher risk disease",
                        "recommendations": [
                            {
                                "therapy": "Anthracycline and taxane-based chemotherapy",
                                "details": "With Trastuzumab + Pertuzumab"
                            },
                            {
                                "therapy": "Consider extended HER2 therapy",
                                "details": "Neratinib after Trastuzumab"
                            }
                        ]
                    },
                    "4": {
                        "name": "Maximum Intensity Therapy",
                        "description": "For highest risk disease",
                        "recommendations": [
                            {
                                "therapy": "Dose-dense chemotherapy",
                                "details": "With dual HER2 blockade (Trastuzumab + Pertuzumab)"
                            },
                            {
                                "therapy": "Extended HER2-targeted therapy",
                                "details": "Consider T-DM1 or novel agents in high-risk cases"
                            }
                        ]
                    }
                }
            },
            "HER2 Enriched": {
                "description": "Hormone receptor negative, HER2 positive breast cancer",
                "therapy_levels": {
                    "1": {
                        "name": "Low Intensity Therapy",
                        "description": "For very small, node-negative tumors",
                        "recommendations": [
                            {
                                "therapy": "Taxane + HER2-targeted therapy",
                                "details": "Paclitaxel + Trastuzumab"
                            }
                        ]
                    },
                    "2": {
                        "name": "Standard Therapy",
                        "description": "Standard approach for most patients",
                        "recommendations": [
                            {
                                "therapy": "Chemotherapy + dual HER2 blockade",
                                "details": "Taxane-based regimen with Trastuzumab + Pertuzumab"
                            }
                        ]
                    },
                    "3": {
                        "name": "Intensified Therapy",
                        "description": "For higher risk disease",
                        "recommendations": [
                            {
                                "therapy": "Anthracycline and taxane-based chemotherapy",
                                "details": "With Trastuzumab + Pertuzumab"
                            },
                            {
                                "therapy": "Consider additional HER2-targeted therapy",
                                "details": "Extended therapy or additional agents"
                            }
                        ]
                    },
                    "4": {
                        "name": "Maximum Intensity Therapy",
                        "description": "For highest risk disease",
                        "recommendations": [
                            {
                                "therapy": "Dose-dense or dose-intense chemotherapy",
                                "details": "With dual HER2 blockade"
                            },
                            {
                                "therapy": "Consider novel HER2-targeted approaches",
                                "details": "T-DM1, newer TKIs, or clinical trials"
                            }
                        ]
                    }
                }
            },
            "Triple Negative": {
                "description": "Hormone receptor negative, HER2 negative breast cancer",
                "therapy_levels": {
                    "1": {
                        "name": "Low Intensity Therapy",
                        "description": "For very small, node-negative tumors",
                        "recommendations": [
                            {
                                "therapy": "Chemotherapy",
                                "details": "Consider TC or AC regimen"
                            }
                        ]
                    },
                    "2": {
                        "name": "Standard Therapy",
                        "description": "Standard approach for most patients",
                        "recommendations": [
                            {
                                "therapy": "Anthracycline and taxane-based chemotherapy",
                                "details": "Consider dose-dense scheduling"
                            },
                            {
                                "therapy": "Consider platinum agent",
                                "details": "Especially for BRCA-associated tumors"
                            }
                        ]
                    },
                    "3": {
                        "name": "Intensified Therapy",
                        "description": "For higher risk disease",
                        "recommendations": [
                            {
                                "therapy": "Dose-dense chemotherapy",
                                "details": "With inclusion of platinum agent"
                            },
                            {
                                "therapy": "Consider immunotherapy",
                                "details": "Pembrolizumab for eligible patients"
                            }
                        ]
                    },
                    "4": {
                        "name": "Maximum Intensity Therapy",
                        "description": "For highest risk disease",
                        "recommendations": [
                            {
                                "therapy": "Dose-dense, dose-intense chemotherapy",
                                "details": "With platinum agent"
                            },
                            {
                                "therapy": "Consider PARP inhibitors",
                                "details": "For BRCA-associated disease"
                            },
                            {
                                "therapy": "Immunotherapy",
                                "details": "Pembrolizumab for eligible patients"
                            }
                        ]
                    }
                }
            }
        },
        "special_biomarkers": {
            "BRCA1_mutation": {
                "clinical_significance": "Hereditary breast cancer risk gene, associated with DNA repair deficiency",
                "therapy_options": [
                    {
                        "name": "PARP inhibitor",
                        "indication": "Olaparib or Talazoparib for metastatic disease"
                    },
                    {
                        "name": "Platinum chemotherapy",
                        "indication": "Increased sensitivity due to DNA repair deficiency"
                    }
                ]
            },
            "BRCA2_mutation": {
                "clinical_significance": "Hereditary breast cancer risk gene, associated with DNA repair deficiency",
                "therapy_options": [
                    {
                        "name": "PARP inhibitor",
                        "indication": "Olaparib or Talazoparib for metastatic disease"
                    },
                    {
                        "name": "Platinum chemotherapy",
                        "indication": "Increased sensitivity due to DNA repair deficiency"
                    }
                ]
            },
            "PIK3CA_mutation": {
                "clinical_significance": "Common mutation in ER+ breast cancer, activates PI3K pathway",
                "therapy_options": [
                    {
                        "name": "Alpelisib",
                        "indication": "PI3K inhibitor for PIK3CA-mutated, HR+/HER2- advanced breast cancer"
                    }
                ]
            },
            "ERBB2_amplification": {
                "clinical_significance": "Gene encoding HER2, amplification leads to HER2 overexpression",
                "therapy_options": [
                    {
                        "name": "Trastuzumab",
                        "indication": "First-line HER2-targeted antibody"
                    },
                    {
                        "name": "Pertuzumab",
                        "indication": "Additional HER2-targeted antibody, often used with trastuzumab"
                    },
                    {
                        "name": "T-DM1",
                        "indication": "Antibody-drug conjugate for HER2+ disease"
                    }
                ]
            },
            "PTEN_loss": {
                "clinical_significance": "Tumor suppressor gene, loss activates PI3K/AKT pathway",
                "therapy_options": [
                    {
                        "name": "AKT inhibitors",
                        "indication": "Clinical trials for PTEN-deficient tumors"
                    },
                    {
                        "name": "mTOR inhibitors",
                        "indication": "Everolimus for hormone receptor positive disease"
                    }
                ]
            }
        },
        "therapy_levels": {
            "1": {
                "name": "Low Intensity Therapy",
                "description": "Conservative approach for low-risk disease",
                "follow_up": "Every 4-6 months for 5 years, then annually",
                "monitoring": "Annual mammogram, symptom monitoring"
            },
            "2": {
                "name": "Standard Therapy",
                "description": "Balanced approach for most patients",
                "follow_up": "Every 3-4 months for 3 years, then every 6 months for 2 years, then annually",
                "monitoring": "Annual mammogram, consider tumor marker monitoring"
            },
            "3": {
                "name": "Intensified Therapy",
                "description": "More aggressive approach for high-risk disease",
                "follow_up": "Every 3 months for 2 years, then every 4 months for 3 years, then every 6 months",
                "monitoring": "Annual mammogram, consider more frequent imaging in high-risk areas"
            },
            "4": {
                "name": "Maximum Intensity Therapy",
                "description": "Most aggressive approach for very high-risk disease",
                "follow_up": "Every 2-3 months for 3 years, then every 4 months for 2 years, then every 6 months",
                "monitoring": "Annual mammogram, consider CT/PET in symptomatic areas, tumor marker monitoring"
            }
        }
    }
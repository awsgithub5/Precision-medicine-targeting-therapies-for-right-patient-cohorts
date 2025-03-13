"""
Functions for generating therapy recommendations
"""

from modules.breast_cancer import get_breast_cancer_recommendations
from modules.lung_cancer import get_lung_cancer_recommendations

def get_therapy_recommendations(patient_data, knowledge_base, cancer_type):
    """
    Get specific therapy recommendations based on the patient's molecular profile
    Args:
        patient_data: Dictionary or Series with patient's molecular profile
        knowledge_base: Dictionary with therapy knowledge base
        cancer_type: Type of cancer ("Breast Cancer" or "Lung Cancer")
    Returns:
        Tuple of (base_recommendations, special_recommendations)
    """
    if cancer_type == "Breast Cancer":
        return get_breast_cancer_recommendations(patient_data, knowledge_base)
    else:  # Lung Cancer
        return get_lung_cancer_recommendations(patient_data, knowledge_base)

def get_breast_cancer_recommendations(patient_data, knowledge_base):
    """
    Get therapy recommendations for breast cancer patients
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

def get_lung_cancer_recommendations(patient_data, knowledge_base):
    """
    Get therapy recommendations for lung cancer patients
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
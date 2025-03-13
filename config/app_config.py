"""
Configuration settings for the Precision Oncology Application
"""

# App display settings
APP_TITLE = "Precision Oncology: Therapy Targeting System"
APP_ICON = "🧬"
APP_LAYOUT = "wide"

# Data file paths
BREAST_CANCER_KNOWLEDGE_BASE_PATH = "data/Breasts_therapy_knowledge_base.json"
LUNG_CANCER_KNOWLEDGE_BASE_PATH = "data/lung_therapy_knowledge_base.json"
BREAST_CANCER_PATIENT_DATA_PATH = "data/BREAST_PATIENT_DATA_oncoprint.tsv"
LUNG_CANCER_PATIENT_DATA_PATH = "data/LUNG_PATIENT_DATA_oncoprint.tsv"

# Cancer types supported by the application
CANCER_TYPES = ["Breast Cancer", "Lung Cancer"]

# Key genes for each cancer type
BREAST_CANCER_KEY_GENES = ["BRCA1", "BRCA2", "TP53", "PIK3CA", "ESR1", "ERBB2", "MYC", "CCND1", "RB1", "PTEN"]
LUNG_CANCER_KEY_GENES = ["EGFR", "ALK", "ROS1", "KRAS", "TP53", "MET", "RET", "BRAF", "HER2", "NTRK"]

# Azure OpenAI configuration
AZURE_OPENAI_API_VERSION = "2023-09-15-preview"
AZURE_OPENAI_DEPLOYMENT = "gpt-4o"
AZURE_OPENAI_TEMPERATURE = 0.2
AZURE_OPENAI_MAX_TOKENS = 1000

# Tabs in the application
TABS = ["Patient Lookup", "Dashboard", "Database", "New Patient"]
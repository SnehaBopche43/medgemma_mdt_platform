import json
from pathlib import Path

def generate_lung_cancer_case():
    """Generate a realistic lung cancer case"""
    
    case = {
        "patient_id": "LC-002",
        "cancer_type": "Lung Cancer (Non-Small Cell)",
        "demographics": {
            "age": 67,
            "sex": "Male",
            "smoking_history": "Former smoker, 40 pack-years, quit 5 years ago",
            "medical_history": "COPD, hypertension, no prior cancer history"
        },
        "imaging": {
            "modality": "CT Chest with Contrast",
            "findings": [
                "4.5 cm spiculated mass in right upper lobe",
                "Mass abuts the pleural surface with possible chest wall invasion",
                "Enlarged right hilar lymph nodes (largest 2.3 cm)",
                "Mediastinal lymphadenopathy, subcarinal node 1.8 cm",
                "No distant metastasis identified in chest, liver, or adrenals"
            ],
            "impression": "Suspicious for primary lung malignancy with regional lymph node involvement, clinical Stage IIIA"
        },
        "pathology": {
            "biopsy_site": "CT-guided lung biopsy",
            "histology": "Adenocarcinoma",
            "grade": "Moderately differentiated (Grade 2)",
            "molecular_markers": {
                "EGFR": "Negative (wild-type)",
                "ALK": "Negative",
                "PD-L1": "60% (high expression)",
                "ROS1": "Negative",
                "KRAS": "G12C mutation detected"
            },
            "diagnosis": "Non-small cell lung cancer, adenocarcinoma, Stage IIIA (T3N2M0)"
        },
        "staging": {
            "tnm": "T3N2M0",
            "stage": "Stage IIIA",
            "ajcc_version": "8th edition",
            "details": {
                "T": "T3 - Tumor >4cm, invading chest wall",
                "N": "N2 - Ipsilateral mediastinal lymph nodes",
                "M": "M0 - No distant metastasis"
            }
        },
        "lab_results": {
            "CEA": "8.2 ng/mL (elevated)",
            "Hemoglobin": "12.1 g/dL (mild anemia)",
            "Albumin": "3.4 g/dL (low normal)",
            "LDH": "245 U/L (normal)",
            "Creatinine": "1.1 mg/dL (normal)"
        },
        "pulmonary_function": {
            "FEV1": "62% predicted (moderate obstruction)",
            "DLCO": "58% predicted (reduced diffusion capacity)",
            "assessment": "Moderate COPD, surgical candidate with risk"
        },
        "clinical_notes": "67-year-old male former smoker presenting with persistent cough and weight loss. CT reveals 4.5 cm right upper lobe mass with mediastinal lymphadenopathy. Biopsy confirms adenocarcinoma with KRAS G12C mutation and high PD-L1 expression. Staging workup shows locally advanced disease (Stage IIIA) without distant metastasis. Patient has moderate COPD but is deemed surgical candidate. Requires multidisciplinary discussion for optimal treatment sequencing.",
        "performance_status": {
            "ecog": 1,
            "description": "Symptomatic but ambulatory, capable of light work"
        }
    }
    
    return case


def save_case(case, filename):
    output_dir = Path("data/synthetic_cases")
    output_dir.mkdir(parents=True, exist_ok=True)
    filepath = output_dir / filename
    with open(filepath, 'w') as f:
        json.dump(case, f, indent=2)
    return filepath

def main():
    print("Generating case...")
    case = generate_lung_cancer_case()
    filepath = save_case(case, "case_002.json")
    print(f"Saved to: {filepath}")

if __name__ == "__main__":
    main()

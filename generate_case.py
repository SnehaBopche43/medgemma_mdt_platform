import json
from pathlib import Path

def generate_breast_cancer_case():
    """Generate a realistic breast cancer case for testing"""
    
    case = {
        "patient_id": "BC-001",
        "cancer_type": "Breast Cancer",
        "demographics": {
            "age": 52,
            "sex": "Female",
            "medical_history": "Hypertension, no prior cancer history"
        },
        "imaging": {
            "modality": "CT Chest with Contrast",
            "findings": [
                "3.2 cm irregular mass in upper outer quadrant of right breast",
                "Spiculated margins suggesting malignancy",
                "Enlarged right axillary lymph nodes (largest 1.8 cm)",
                "No evidence of distant metastasis in chest"
            ],
            "impression": "Suspicious for invasive breast carcinoma with lymph node involvement"
        },
        "pathology": {
            "biopsy_site": "Right breast mass",
            "diagnosis": "Invasive Ductal Carcinoma",
            "grade": "Grade 2 (moderately differentiated)",
            "receptors": {
                "ER": "Positive (90%)",
                "PR": "Positive (70%)",
                "HER2": "Negative"
            },
            "ki67": "25%"
        },
        "labs": {
            "CBC": "Within normal limits",
            "LFTs": "Normal",
            "tumor_markers": {
                "CA 15-3": "32 U/mL (slightly elevated)"
            }
        },
        "clinical_notes": "52-year-old woman presents with palpable right breast mass discovered on self-examination 2 months ago. No family history of breast cancer. Performance status ECOG 0.",
        "staging": {
            "T": "T2 (tumor 2-5 cm)",
            "N": "N1 (1-3 axillary lymph nodes)",
            "M": "M0 (no distant metastasis)",
            "stage": "Stage IIB"
        }
    }
    
    return case

def save_case(case, filename):
    """Save case to JSON file"""
    output_dir = Path("data/synthetic_cases")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    filepath = output_dir / filename
    with open(filepath, 'w') as f:
        json.dump(case, f, indent=2)
    
    print(f"Case saved to: {filepath}")
    return filepath

def main():
    print("=" * 60)
    print("Generating Synthetic Cancer Case")
    print("=" * 60)
    
    case = generate_breast_cancer_case()
    filepath = save_case(case, "case_001.json")
    
    print("\nCase Summary:")
    print(f"  Patient ID: {case['patient_id']}")
    print(f"  Cancer Type: {case['cancer_type']}")
    print(f"  Stage: {case['staging']['stage']}")
    print(f"  Receptors: ER+/PR+/HER2-")
    
    print("\n" + "=" * 60)
    print("Case generation complete!")
    print("=" * 60)
    print(f"\nTo process this case, run:")
    print(f"  python main.py --case {filepath}")

if __name__ == "__main__":
    main()

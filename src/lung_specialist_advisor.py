"""
Lung Cancer Specialist Advisor Module
Uses MedGemma to provide treatment recommendations for lung cancer MDT
"""

from transformers import AutoTokenizer, AutoModelForCausalLM
import torch

class LungSpecialistAdvisor:
    def __init__(self):
        print("Loading MedGemma model...")
        self.model_name = "google/medgemma-4b-it"
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        self.model = AutoModelForCausalLM.from_pretrained(
            self.model_name,
            torch_dtype=torch.float32,
            low_cpu_mem_usage=True
        )
        print("MedGemma model loaded successfully!")
    
    def generate_recommendations(self, case_data):
        """Generate treatment recommendations using MedGemma"""
        
        # Extract key information
        patient = case_data["patient_info"]
        diagnosis = case_data["diagnosis"]
        pathology = case_data["pathology"]
        molecular = case_data["molecular_testing"]
        imaging = case_data["imaging"]
        
        # Build comprehensive prompt
        prompt = f"""You are a thoracic oncologist providing treatment recommendations for a lung cancer MDT meeting.

PATIENT INFORMATION:
- Age: {patient["age"]} years
- Gender: {patient["gender"]}
- Performance Status: ECOG {patient["performance_status"]}
- Smoking History: {patient["smoking_history"]}

DIAGNOSIS:
- Primary Site: {diagnosis["primary_site"]}
- Histology: {diagnosis["histology"]}
- Stage: {diagnosis["stage"]}

PATHOLOGY:
- Tumor Size: {pathology["tumor_size"]}
- Grade: {pathology["grade"]}
- Lymphovascular Invasion: {pathology["lymphovascular_invasion"]}
- Perineural Invasion: {pathology["perineural_invasion"]}

MOLECULAR TESTING:
- PD-L1 Expression: {molecular["pdl1_expression"]}
- Driver Mutations: {", ".join(molecular["driver_mutations"]) if molecular["driver_mutations"] else "None detected"}
- Additional Markers: {", ".join([f"{k}: {v}" for k, v in molecular["additional_markers"].items()])}

IMAGING FINDINGS:
- Modality: {imaging["modality"]}
- Impression: {imaging["impression"]}

Please provide:
1. Treatment intent (curative vs palliative)
2. Recommended treatment approach:
   - Surgery options (if applicable)
   - Radiation therapy (type, dose, technique)
   - Systemic therapy (chemotherapy, targeted therapy, immunotherapy)
   - Multimodal sequencing
3. Rationale based on stage, molecular profile, and patient factors
4. Clinical trial eligibility considerations
5. Expected outcomes and prognosis
6. Follow-up imaging and monitoring plan

Treatment Recommendations:"""
        
        # Generate response
        inputs = self.tokenizer(prompt, return_tensors="pt")
        outputs = self.model.generate(
            **inputs,
            max_new_tokens=500,
            temperature=0.7,
            do_sample=True
        )
        
        response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        # Extract recommendations
        if "Treatment Recommendations:" in response:
            recommendations = response.split("Treatment Recommendations:")[-1].strip()
        else:
            recommendations = response
        
        return {
            "stage": diagnosis["stage"],
            "histology": diagnosis["histology"],
            "molecular_profile": {
                "pdl1": molecular["pdl1_expression"],
                "driver_mutations": molecular["driver_mutations"]
            },
            "treatment_recommendations": recommendations,
            "performance_status": patient["performance_status"]
        }

def main():
    """Test the lung specialist advisor"""
    import json
    from pathlib import Path
    
    print("=" * 60)
    print("Testing Lung Cancer Specialist Advisor Module")
    print("=" * 60)
    
    # Load lung cancer test case
    case_path = Path("data/synthetic_cases/case_002.json")
    with open(case_path, 'r') as f:
        case_data = json.load(f)
    
    # Generate recommendations
    advisor = LungSpecialistAdvisor()
    result = advisor.generate_recommendations(case_data)
    
    print("\nLung Cancer Treatment Recommendations:")
    print("-" * 60)
    print(result["treatment_recommendations"])
    print("-" * 60)
    
    # Save result
    output_dir = Path("outputs/evaluations")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    output_path = output_dir / "lung_treatment_recommendations_002.json"
    with open(output_path, 'w') as f:
        json.dump(result, f, indent=2)
    
    print(f"\nRecommendations saved to: {output_path}")

if __name__ == "__main__":
    main()

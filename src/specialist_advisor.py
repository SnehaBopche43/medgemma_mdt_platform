"""
Specialist Advisor Module
Medical Oncologist using MedGemma for treatment recommendations
"""

from transformers import AutoTokenizer, AutoModelForCausalLM
import torch

class MedicalOncologist:
    def __init__(self):
        print("Loading MedGemma model for Medical Oncology...")
        self.model_name = "google/medgemma-4b-it"
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        self.model = AutoModelForCausalLM.from_pretrained(
            self.model_name,
            torch_dtype=torch.float32,
            low_cpu_mem_usage=True
        )
        print("Medical Oncologist agent ready!")
    
    def provide_recommendation(self, case_data):
        """Generate treatment recommendations based on case data"""
        
        # Extract key information
        cancer_type = case_data.get("cancer_type", "Unknown")
        staging = case_data.get("staging", {})
        pathology = case_data.get("pathology", {})
        demographics = case_data.get("demographics", {})
        
        # Build comprehensive prompt
        prompt = f"""You are a Medical Oncologist providing treatment recommendations for an MDT meeting.

Patient Information:
- Age: {demographics.get('age', 'Unknown')}
- Cancer Type: {cancer_type}
- Stage: {staging.get('stage', 'Unknown')} ({staging.get('T', 'Unknown')}, {staging.get('N', 'Unknown')}, {staging.get('M', 'Unknown')})

Pathology:
- Diagnosis: {pathology.get('diagnosis', 'Unknown')}
- Grade: {pathology.get('grade', 'Unknown')}
- ER: {pathology.get('receptors', {}).get('ER', 'Unknown')}
- PR: {pathology.get('receptors', {}).get('PR', 'Unknown')}
- HER2: {pathology.get('receptors', {}).get('HER2', 'Unknown')}
- Ki-67: {pathology.get('ki67', 'Unknown')}

As the Medical Oncologist, please provide:

1. Treatment Strategy:
   - Recommended systemic therapy approach
   - Specific chemotherapy regimen if indicated
   - Hormonal therapy recommendations
   - Targeted therapy considerations

2. Treatment Sequencing:
   - Neoadjuvant vs adjuvant approach
   - Timing relative to surgery/radiation

3. Clinical Trial Eligibility:
   - Relevant clinical trials to consider

4. Prognosis and Expected Outcomes:
   - 5-year survival estimates
   - Response expectations

Medical Oncology Recommendation:"""
        
        # Generate recommendation
        inputs = self.tokenizer(prompt, return_tensors="pt")
        outputs = self.model.generate(
            **inputs,
            max_new_tokens=400,
            temperature=0.7,
            do_sample=True
        )
        
        response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        # Extract recommendation
        if "Medical Oncology Recommendation:" in response:
            recommendation = response.split("Medical Oncology Recommendation:")[-1].strip()
        else:
            recommendation = response
        
        return {
            "specialty": "Medical Oncology",
            "case_summary": {
                "cancer_type": cancer_type,
                "stage": staging.get('stage', 'Unknown'),
                "receptors": pathology.get('receptors', {})
            },
            "recommendation": recommendation
        }

def main():
    """Test the Medical Oncologist agent"""
    import json
    from pathlib import Path
    
    print("=" * 60)
    print("Testing Medical Oncologist Agent")
    print("=" * 60)
    
    # Load test case
    case_path = Path("data/synthetic_cases/case_001.json")
    with open(case_path, 'r') as f:
        case_data = json.load(f)
    
    # Get oncologist recommendation
    oncologist = MedicalOncologist()
    result = oncologist.provide_recommendation(case_data)
    
    print("\nMedical Oncology Recommendation:")
    print("-" * 60)
    print(result["recommendation"])
    print("-" * 60)
    
    # Save result
    output_dir = Path("outputs/evaluations")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    output_path = output_dir / "oncology_recommendation_001.json"
    with open(output_path, 'w') as f:
        json.dump(result, f, indent=2)
    
    print(f"\nRecommendation saved to: {output_path}")

if __name__ == "__main__":
    main()

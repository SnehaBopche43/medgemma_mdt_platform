"""
Colorectal Cancer MDT Case Brief Generator
Synthesizes multi-agent analysis into comprehensive MDT presentation
"""

from transformers import AutoTokenizer, AutoModelForCausalLM
import torch
import json
from pathlib import Path

class ColorectalMDTBriefGenerator:
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
    
    def generate_mdt_brief(self, case_data, imaging_analysis, treatment_recommendations):
        """Generate comprehensive MDT brief using MedGemma"""
        
        patient = case_data["patient_info"]
        diagnosis = case_data["diagnosis"]
        
        prompt = f"""You are preparing a comprehensive case brief for a colorectal cancer MDT meeting.

CASE SUMMARY:
Patient: {patient["age"]}-year-old {patient["gender"]}
Diagnosis: {diagnosis["stage"]} {diagnosis["histology"]}
Primary Site: {diagnosis["primary_site"]}

RADIOLOGY ANALYSIS:
{imaging_analysis["ai_analysis"]}

TREATMENT RECOMMENDATIONS:
{treatment_recommendations["treatment_recommendations"]}

Please synthesize this information into a structured MDT brief including:
1. Case summary (one paragraph)
2. Key clinical and pathological features
3. Imaging highlights (primary tumor, lymph nodes, metastases)
4. Molecular profile and treatment implications
5. Proposed treatment plan with rationale
6. Discussion points for MDT consideration
7. Follow-up recommendations

MDT Brief:"""
        
        # Generate response
        inputs = self.tokenizer(prompt, return_tensors="pt")
        outputs = self.model.generate(
            **inputs,
            max_new_tokens=600,
            temperature=0.7,
            do_sample=True
        )
        
        response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        # Extract brief
        if "MDT Brief:" in response:
            mdt_brief = response.split("MDT Brief:")[-1].strip()
        else:
            mdt_brief = response
        
        return {
            "case_id": case_data.get("case_id", "Unknown"),
            "patient_summary": f"{patient['age']}-year-old {patient['gender']} with {diagnosis['stage']} {diagnosis['histology']}",
            "stage": diagnosis["stage"],
            "histology": diagnosis["histology"],
            "mdt_brief": mdt_brief,
            "imaging_analysis": imaging_analysis,
            "treatment_recommendations": treatment_recommendations
        }

def main():
    """Test the colorectal MDT brief generator"""
    print("=" * 60)
    print("Testing Colorectal Cancer MDT Brief Generator")
    print("=" * 60)
    
    # Load case data
    case_path = Path("data/synthetic_cases/case_003.json")
    with open(case_path, 'r') as f:
        case_data = json.load(f)
    
    # Load imaging analysis
    imaging_path = Path("outputs/evaluations/colorectal_imaging_analysis_003.json")
    if imaging_path.exists():
        with open(imaging_path, 'r') as f:
            imaging_analysis = json.load(f)
    else:
        print("\nWarning: Imaging analysis not found. Run colorectal_image_analysis.py first.")
        print("Using placeholder data for demonstration...")
        imaging_analysis = {
            "ai_analysis": "Placeholder imaging analysis - run colorectal_image_analysis.py to generate actual analysis"
        }
    
    # Load treatment recommendations
    treatment_path = Path("outputs/evaluations/colorectal_treatment_recommendations_003.json")
    if treatment_path.exists():
        with open(treatment_path, 'r') as f:
            treatment_recommendations = json.load(f)
    else:
        print("\nWarning: Treatment recommendations not found. Run colorectal_specialist_advisor.py first.")
        print("Using placeholder data for demonstration...")
        treatment_recommendations = {
            "treatment_recommendations": "Placeholder treatment recommendations - run colorectal_specialist_advisor.py to generate actual recommendations"
        }
    
    # Generate MDT brief
    generator = ColorectalMDTBriefGenerator()
    result = generator.generate_mdt_brief(case_data, imaging_analysis, treatment_recommendations)
    
    print("\nColorectal Cancer MDT Brief:")
    print("-" * 60)
    print(result["mdt_brief"])
    print("-" * 60)
    
    # Save result
    output_dir = Path("outputs/mdt_briefs")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    output_path = output_dir / "colorectal_mdt_brief_003.json"
    with open(output_path, 'w') as f:
        json.dump(result, f, indent=2)
    
    print(f"\nMDT Brief saved to: {output_path}")
    
    # Also save as readable text file
    text_output_path = output_dir / "colorectal_mdt_brief_003.txt"
    with open(text_output_path, 'w') as f:
        f.write("=" * 60 + "\n")
        f.write("COLORECTAL CANCER MDT CASE BRIEF\n")
        f.write("=" * 60 + "\n\n")
        f.write(f"Case ID: {result['case_id']}\n")
        f.write(f"Patient: {result['patient_summary']}\n")
        f.write(f"Stage: {result['stage']}\n")
        f.write(f"Histology: {result['histology']}\n\n")
        f.write("-" * 60 + "\n")
        f.write("MDT BRIEF\n")
        f.write("-" * 60 + "\n\n")
        f.write(result['mdt_brief'])
        f.write("\n\n")
    
    print(f"Readable brief saved to: {text_output_path}")

if __name__ == "__main__":
    main()

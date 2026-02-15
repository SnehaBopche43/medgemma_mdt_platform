"""
Lung Cancer Image Analysis Module
Uses MedGemma to analyze CT chest imaging findings for lung cancer MDT
"""

from transformers import AutoTokenizer, AutoModelForCausalLM
import torch

class LungImageAnalyzer:
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
    
    def analyze_imaging(self, imaging_data):
        """Analyze lung cancer imaging findings using MedGemma"""
        
        # Create prompt for MedGemma
        findings_text = "\n".join(imaging_data["findings"])
        
        prompt = f"""You are a thoracic radiologist analyzing CT chest imaging for a lung cancer MDT meeting.

Imaging Modality: {imaging_data["modality"]}

Findings:
{findings_text}

Radiologist Impression: {imaging_data["impression"]}

Please provide:
1. Primary tumor characteristics (size, location, growth pattern)
2. Lymph node involvement and mediastinal assessment
3. Evidence of local invasion (pleura, chest wall, mediastinum)
4. Metastatic disease evaluation
5. TNM staging assessment based on imaging
6. Recommended additional imaging if needed (brain MRI, PET-CT, etc.)

Analysis:"""
        
        # Generate response
        inputs = self.tokenizer(prompt, return_tensors="pt")
        outputs = self.model.generate(
            **inputs,
            max_new_tokens=400,
            temperature=0.7,
            do_sample=True
        )
        
        response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        # Extract just the analysis part (after "Analysis:")
        if "Analysis:" in response:
            analysis = response.split("Analysis:")[-1].strip()
        else:
            analysis = response
        
        return {
            "modality": imaging_data["modality"],
            "findings": imaging_data["findings"],
            "ai_analysis": analysis,
            "impression": imaging_data["impression"]
        }

def main():
    """Test the lung image analyzer"""
    import json
    from pathlib import Path
    
    print("=" * 60)
    print("Testing Lung Cancer Image Analysis Module")
    print("=" * 60)
    
    # Load lung cancer test case
    case_path = Path("data/synthetic_cases/case_002.json")
    with open(case_path, 'r') as f:
        case_data = json.load(f)
    
    # Analyze imaging
    analyzer = LungImageAnalyzer()
    result = analyzer.analyze_imaging(case_data["imaging"])
    
    print("\nLung Cancer Imaging Analysis Result:")
    print("-" * 60)
    print(result["ai_analysis"])
    print("-" * 60)
    
    # Save result
    output_dir = Path("outputs/evaluations")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    output_path = output_dir / "lung_imaging_analysis_002.json"
    with open(output_path, 'w') as f:
        json.dump(result, f, indent=2)
    
    print(f"\nAnalysis saved to: {output_path}")

if __name__ == "__main__":
    main()

"""
Image Analysis Module
Uses MedGemma to analyze medical imaging findings
"""

from transformers import AutoTokenizer, AutoModelForCausalLM
import torch

class ImageAnalyzer:
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
        """Analyze imaging findings using MedGemma"""
        
        # Handle both full case_data and just imaging section
        if "imaging" in imaging_data:
            imaging_section = imaging_data["imaging"]
        else:
            imaging_section = imaging_data
        
        # Safe extraction of findings
        findings = imaging_section.get("findings", [])
        if isinstance(findings, list):
            findings_text = "\n".join(findings) if findings else "No findings available"
        elif isinstance(findings, str):
            findings_text = findings
        else:
            findings_text = "No findings available"
        
        modality = imaging_section.get("modality", "Not specified")
        impression = imaging_section.get("impression", "No impression provided")
        
        # Create prompt for MedGemma
        prompt = f"""You are a radiologist analyzing medical imaging for an MDT meeting.

Imaging Modality: {modality}

Findings:
{findings_text}

Radiologist Impression: {impression}

Please provide:
1. Key imaging features for staging
2. Evidence of local invasion or metastasis
3. Recommended additional imaging if needed

Analysis:"""
        
        # Generate response
        inputs = self.tokenizer(prompt, return_tensors="pt")
        outputs = self.model.generate(
            **inputs,
            max_new_tokens=300,
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
            "modality": modality,
            "findings": findings,
            "ai_analysis": analysis,
            "impression": impression
        }

def main():
    """Test the image analyzer"""
    import json
    from pathlib import Path
    
    print("=" * 60)
    print("Testing Image Analysis Module")
    print("=" * 60)
    
    # Load test case
    case_path = Path("data/synthetic_cases/case_001.json")
    with open(case_path, 'r') as f:
        case_data = json.load(f)
    
    # Analyze imaging
    analyzer = ImageAnalyzer()
    result = analyzer.analyze_imaging(case_data["imaging"])
    
    print("\nImaging Analysis Result:")
    print("-" * 60)
    print(result["ai_analysis"])
    print("-" * 60)
    
    # Save result
    output_dir = Path("outputs/evaluations")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    output_path = output_dir / "imaging_analysis_001.json"
    with open(output_path, 'w') as f:
        json.dump(result, f, indent=2)
    
    print(f"\nAnalysis saved to: {output_path}")

if __name__ == "__main__":
    main()

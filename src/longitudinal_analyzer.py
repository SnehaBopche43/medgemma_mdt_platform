"""
Longitudinal Analysis Module
Analyzes patient data across multiple timepoints to track disease progression and treatment response
"""

from transformers import AutoTokenizer, AutoModelForCausalLM
import torch
import json
from pathlib import Path
from datetime import datetime

class LongitudinalAnalyzer:
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
    
    def analyze_longitudinal_case(self, case_data):
        """
        Analyze longitudinal case data across multiple timepoints
        
        Args:
            case_data: Dictionary containing patient case with multiple timepoints
        
        Returns:
            Dictionary with longitudinal analysis results
        """
        
        case_id = case_data.get("case_id", case_data.get("patient_id", "Unknown"))
        cancer_type = case_data.get("cancer_type", "Unknown")
        timepoints = case_data.get("timepoints", [])
        
        if not timepoints:
            return {
                "error": "No timepoints found in case data",
                "case_id": case_id
            }
        
        print(f"\n{'='*80}")
        print(f"LONGITUDINAL ANALYSIS: {case_id}")
        print(f"Cancer Type: {cancer_type}")
        print(f"Number of Timepoints: {len(timepoints)}")
        print(f"{'='*80}\n")
        
        # Extract key metrics across timepoints
        timeline_summary = self._extract_timeline_metrics(timepoints)
        
        # Generate AI analysis of disease trajectory
        trajectory_analysis = self._analyze_disease_trajectory(
            case_id=case_id,
            cancer_type=cancer_type,
            timeline_summary=timeline_summary,
            timepoints=timepoints
        )
        
        # Compile results
        results = {
            "case_id": case_id,
            "cancer_type": cancer_type,
            "analysis_date": datetime.now().isoformat(),
            "number_of_timepoints": len(timepoints),
            "timeline_summary": timeline_summary,
            "trajectory_analysis": trajectory_analysis,
            "timepoint_details": timepoints
        }
        
        return results
    
    def _extract_timeline_metrics(self, timepoints):
        """Extract key metrics across all timepoints"""
        
        timeline = []
        
        for tp in timepoints:
            timepoint_id = tp.get("timepoint_id", "unknown")
            date = tp.get("date", "unknown")
            description = tp.get("description", "")
            
            # Extract imaging data safely
            imaging = tp.get("imaging", {})
            imaging_findings = imaging.get("findings", [])
            if isinstance(imaging_findings, list):
                imaging_summary = "; ".join(imaging_findings[:2])  # First 2 findings
            else:
                imaging_summary = str(imaging_findings)
            
            # Extract tumor size from pathology or imaging
            tumor_size = "N/A"
            pathology = tp.get("pathology", {})
            if pathology and "tumor_size" in pathology:
                tumor_size = pathology.get("tumor_size", "N/A")
            
            # Extract staging
            staging = tp.get("staging", {})
            tnm = staging.get("tnm", "N/A")
            stage = staging.get("stage", "N/A")
            
            # Extract treatment info
            treatment_plan = tp.get("treatment_plan", {})
            treatment_received = tp.get("treatment_received", {})
            current_treatment = tp.get("current_treatment", {})
            
            treatment_summary = "N/A"
            if treatment_plan:
                treatment_summary = treatment_plan.get("regimen", treatment_plan.get("approach", "N/A"))
            elif treatment_received:
                treatment_summary = treatment_received.get("chemoradiation_completed", 
                                                          treatment_received.get("regimen", "N/A"))
            elif current_treatment:
                treatment_summary = current_treatment.get("immunotherapy", 
                                                         current_treatment.get("regimen", "N/A"))
            
            # Extract clinical assessment
            clinical_assessment = tp.get("clinical_assessment", {})
            tumor_response = clinical_assessment.get("tumor_response", "N/A")
            disease_status = clinical_assessment.get("disease_status", "N/A")
            
            timeline.append({
                "timepoint_id": timepoint_id,
                "date": date,
                "description": description,
                "tumor_size": tumor_size,
                "tnm_stage": tnm,
                "overall_stage": stage,
                "treatment": treatment_summary,
                "response": tumor_response if tumor_response != "N/A" else disease_status,
                "imaging_summary": imaging_summary[:100]  # Truncate long summaries
            })
        
        return timeline
    
    def _analyze_disease_trajectory(self, case_id, cancer_type, timeline_summary, timepoints):
        """Use MedGemma to analyze disease trajectory"""
        
        # Format timeline for prompt
        timeline_text = ""
        for i, tp in enumerate(timeline_summary, 1):
            timeline_text += f"\nTimepoint {i} ({tp['date']}):\n"
            timeline_text += f"  - Description: {tp['description']}\n"
            timeline_text += f"  - Tumor Size: {tp['tumor_size']}\n"
            timeline_text += f"  - Stage: {tp['overall_stage']} ({tp['tnm_stage']})\n"
            timeline_text += f"  - Treatment: {tp['treatment']}\n"
            timeline_text += f"  - Response: {tp['response']}\n"
        
        # Create prompt for MedGemma
        prompt = f"""You are an oncologist analyzing longitudinal patient data for an MDT meeting.

Case ID: {case_id}
Cancer Type: {cancer_type}
Number of Timepoints: {len(timepoints)}

Timeline Summary:{timeline_text}

Please provide a comprehensive longitudinal analysis including:
1. Disease trajectory (progression, stable, or regression)
2. Treatment effectiveness assessment
3. Key clinical milestones and turning points
4. Prognosis based on observed trajectory
5. Recommendations for ongoing management

Longitudinal Analysis:"""
        
        # Generate response
        inputs = self.tokenizer(prompt, return_tensors="pt")
        outputs = self.model.generate(
            **inputs,
            max_new_tokens=500,
            temperature=0.7,
            do_sample=True
        )
        
        response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        # Extract analysis
        if "Longitudinal Analysis:" in response:
            analysis = response.split("Longitudinal Analysis:")[-1].strip()
        else:
            analysis = response
        
        return analysis
    
    def save_analysis(self, results, output_dir="outputs/longitudinal"):
        """Save longitudinal analysis results"""
        
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        case_id = results.get("case_id", "unknown")
        
        # Save JSON
        json_file = output_path / f"longitudinal_analysis_{case_id}.json"
        with open(json_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        # Save human-readable text report
        text_file = output_path / f"longitudinal_report_{case_id}.txt"
        with open(text_file, 'w') as f:
            f.write("="*80 + "\n")
            f.write(f"LONGITUDINAL ANALYSIS REPORT\n")
            f.write("="*80 + "\n\n")
            f.write(f"Case ID: {results['case_id']}\n")
            f.write(f"Cancer Type: {results['cancer_type']}\n")
            f.write(f"Analysis Date: {results['analysis_date']}\n")
            f.write(f"Number of Timepoints: {results['number_of_timepoints']}\n\n")
            
            f.write("="*80 + "\n")
            f.write("TIMELINE SUMMARY\n")
            f.write("="*80 + "\n\n")
            
            for i, tp in enumerate(results['timeline_summary'], 1):
                f.write(f"Timepoint {i}: {tp['timepoint_id']} ({tp['date']})\n")
                f.write(f"  Description: {tp['description']}\n")
                f.write(f"  Tumor Size: {tp['tumor_size']}\n")
                f.write(f"  Stage: {tp['overall_stage']} ({tp['tnm_stage']})\n")
                f.write(f"  Treatment: {tp['treatment']}\n")
                f.write(f"  Response: {tp['response']}\n\n")
            
            f.write("="*80 + "\n")
            f.write("AI TRAJECTORY ANALYSIS\n")
            f.write("="*80 + "\n\n")
            f.write(results['trajectory_analysis'])
            f.write("\n\n")
            f.write("="*80 + "\n")
        
        print(f"\n✅ Analysis saved to:")
        print(f"   JSON: {json_file}")
        print(f"   Report: {text_file}")
        
        return json_file, text_file
    
    def display_summary(self, results):
        """Display summary of longitudinal analysis"""
        
        print(f"\n{'='*80}")
        print("LONGITUDINAL ANALYSIS SUMMARY")
        print(f"{'='*80}\n")
        
        print(f"Case: {results['case_id']}")
        print(f"Cancer Type: {results['cancer_type']}")
        print(f"Timepoints Analyzed: {results['number_of_timepoints']}\n")
        
        print("Timeline:")
        print("-" * 80)
        for i, tp in enumerate(results['timeline_summary'], 1):
            print(f"{i}. {tp['date']} - {tp['description']}")
            print(f"   Tumor Size: {tp['tumor_size']} | Stage: {tp['overall_stage']} | Response: {tp['response']}")
        
        print("\n" + "="*80)
        print("AI TRAJECTORY ANALYSIS")
        print("="*80)
        print(results['trajectory_analysis'])
        print("="*80 + "\n")


def main():
    """Test longitudinal analyzer"""
    
    print("\n" + "="*80)
    print("LONGITUDINAL ANALYSIS MODULE TEST")
    print("="*80 + "\n")
    
    # Load longitudinal case
    case_file = Path("data/synthetic_cases/case_001_longitudinal.json")
    
    if not case_file.exists():
        print(f"❌ ERROR: Case file not found: {case_file}")
        print("Please create a longitudinal case file first.")
        return
    
    with open(case_file, 'r') as f:
        case_data = json.load(f)
    
    # Initialize analyzer
    analyzer = LongitudinalAnalyzer()
    
    # Analyze case
    results = analyzer.analyze_longitudinal_case(case_data)
    
    # Display summary
    analyzer.display_summary(results)
    
    # Save results
    analyzer.save_analysis(results)
    
    print("\n✅ Longitudinal analysis complete!")


if __name__ == "__main__":
    main()

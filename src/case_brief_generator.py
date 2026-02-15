"""
Case Brief Generator - Simplified Version
"""

import json
from pathlib import Path
from datetime import datetime

class CaseBriefGenerator:
    def __init__(self):
        self.output_dir = Path("outputs/case_briefs")
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def generate_mdt_brief(self, case_data, imaging_analysis, specialist_recommendations):
        """
        Generate MDT brief from provided data (for pipeline integration)
        
        Args:
            case_data: Full case data dictionary
            imaging_analysis: Imaging analysis results
            specialist_recommendations: Specialist recommendations
        
        Returns:
            Dictionary with MDT brief content
        """
        
        case_id = case_data.get('patient_id', case_data.get('case_id', 'Unknown'))
        cancer_type = case_data.get('cancer_type', 'Unknown')
        demographics = case_data.get('demographics', case_data.get('patient_info', {}))
        staging = case_data.get('staging', {})
        pathology = case_data.get('pathology', {})
        
        # Extract imaging findings
        imaging_summary = "Not available"
        if imaging_analysis:
            imaging_summary = imaging_analysis.get('ai_analysis', 
                                                   imaging_analysis.get('impression', 'Not available'))
        
        # Extract specialist recommendations
        specialist_summary = "Not available"
        if specialist_recommendations:
            specialist_summary = specialist_recommendations.get('recommendation', 'Not available')
        
        # Create comprehensive brief
        brief_content = f"""# MDT Case Brief

**Date:** {datetime.now().strftime('%Y-%m-%d')}  
**Patient ID:** {case_id}  
**Cancer Type:** {cancer_type}

---

## Patient Demographics

- Age: {demographics.get('age', 'Unknown')}
- Sex: {demographics.get('sex', demographics.get('gender', 'Unknown'))}
- Medical History: {demographics.get('medical_history', 'Not documented')}

---

## Clinical Summary

**Stage:** {staging.get('stage', 'Unknown')} ({staging.get('T', 'Unknown')}, {staging.get('N', 'Unknown')}, {staging.get('M', 'Unknown')})

**Pathology:**
- Diagnosis: {pathology.get('diagnosis', 'Unknown')}
- Grade: {pathology.get('grade', 'Unknown')}
- Receptors: {pathology.get('receptors', {})}

---

## Imaging Analysis

{imaging_summary}

---

## Medical Oncology Recommendations

{specialist_summary}

---

## MDT Discussion Points

1. **Treatment Intent:** Curative vs Palliative
2. **Sequencing:** Neoadjuvant vs Adjuvant approach
3. **Clinical Trial Eligibility:** Consider available trials
4. **Supportive Care:** Psychosocial and symptom management needs

---

## Consensus Recommendation

**Recommended Approach:**
- Multidisciplinary treatment plan based on stage and biomarkers
- Regular monitoring and response assessment
- Patient-centered care with shared decision making

---

**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        
        # Return as dictionary
        return {
            "case_id": case_id,
            "cancer_type": cancer_type,
            "brief_content": brief_content,
            "executive_summary": f"{cancer_type} - Stage {staging.get('stage', 'Unknown')}",
            "key_discussion_points": [
                "Treatment sequencing",
                "Clinical trial eligibility",
                "Supportive care needs"
            ],
            "consensus_recommendation": "Multidisciplinary treatment plan recommended"
        }
    
    def generate_brief(self, case_id):
        """Generate comprehensive MDT case brief (legacy method)"""
        
        # Load case data
        case_path = Path(f"data/synthetic_cases/{case_id}.json")
        with open(case_path, 'r') as f:
            case_data = json.load(f)
        
        # Load imaging analysis
        case_num = case_id.split('_')[-1]
        imaging_path = Path(f"outputs/evaluations/imaging_analysis_{case_num}.json")
        imaging_analysis = None
        if imaging_path.exists():
            with open(imaging_path, 'r') as f:
                imaging_analysis = json.load(f)
        
        # Load oncology recommendation
        oncology_path = Path(f"outputs/evaluations/oncology_recommendation_{case_num}.json")
        oncology_rec = None
        if oncology_path.exists():
            with open(oncology_path, 'r') as f:
                oncology_rec = json.load(f)
        
        # Generate brief using new method
        brief_result = self.generate_mdt_brief(case_data, imaging_analysis, oncology_rec)
        
        # Save brief
        output_path = self.output_dir / f"mdt_brief_{case_num}.md"
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(brief_result['brief_content'])
        
        print(f"SUCCESS! MDT Case Brief generated!")
        print(f"Location: {output_path}")
        return output_path

def main():
    print("=" * 60)
    print("Generating MDT Case Brief")
    print("=" * 60)
    
    generator = CaseBriefGenerator()
    output_path = generator.generate_brief("case_001")
    
    print("\n" + "=" * 60)
    print("To view the brief:")
    print(f"  cat {output_path}")
    print("=" * 60)

if __name__ == "__main__":
    main()

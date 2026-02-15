"""
Complete Unified MDT Platform
Integrates HITL, References, Validation, and Q&A for all cancer types
"""

import json
from pathlib import Path
from datetime import datetime
from image_analysis import ImageAnalyzer
from specialist_advisor import MedicalOncologist
from case_brief_generator import CaseBriefGenerator
from hitl_approval_system import HITLApprovalSystem
from reference_system import ReferenceSystem
from unified_validation_qa_system import UnifiedValidationQASystem

class CompleteMDTPlatform:
    def __init__(self):
        """Initialize complete MDT platform"""
        print("\n" + "="*80)
        print("🏥 INITIALIZING COMPLETE MDT PLATFORM")
        print("="*80 + "\n")
        
        print("Loading systems...")
        self.hitl = HITLApprovalSystem()
        self.ref_system = ReferenceSystem()
        self.validation_qa = UnifiedValidationQASystem(reference_system=self.ref_system)
        self.imaging_agent = ImageAnalyzer()
        self.specialist_agent = MedicalOncologist()
        self.mdt_brief_agent = CaseBriefGenerator()
        
        print("✅ All systems loaded!\n")
        
        # Cancer-specific configurations
        self.cancer_configs = {
            "breast_cancer": {
                "display_name": "Breast Cancer",
                "icon": "🎗️",
                "imaging_modality": "Mammography/MRI/CT",
                "key_topics": ["neoadjuvant", "adjuvant", "hormonal_therapy", "targeted_therapy"],
                "specialty": "Breast Oncology",
                "common_questions": [
                    "What is the optimal treatment sequencing for this patient?",
                    "Should we consider neoadjuvant vs adjuvant chemotherapy?",
                    "What are the indications for adding CDK4/6 inhibitors?",
                    "What is the expected prognosis and follow-up plan?"
                ]
            },
            "lung_cancer": {
                "display_name": "Lung Cancer",
                "icon": "🫁",
                "imaging_modality": "CT Chest",
                "key_topics": ["immunotherapy", "targeted_therapy", "chemoradiation", "molecular_testing"],
                "specialty": "Thoracic Oncology",
                "common_questions": [
                    "What molecular testing is required before treatment?",
                    "Is the patient eligible for targeted therapy?",
                    "Should we use immunotherapy alone or with chemotherapy?",
                    "What is the role of consolidation therapy?"
                ]
            },
            "colorectal_cancer": {
                "display_name": "Colorectal Cancer",
                "icon": "🎗️",
                "imaging_modality": "CT Abdomen/Pelvis",
                "key_topics": ["adjuvant_therapy", "metastatic_treatment", "molecular_testing"],
                "specialty": "GI Oncology",
                "common_questions": [
                    "What is the role of adjuvant chemotherapy in this stage?",
                    "Should we test for MSI and RAS mutations?",
                    "Is the patient eligible for anti-EGFR therapy?",
                    "What is the optimal surgical approach?"
                ]
            },
            "prostate_cancer": {
                "display_name": "Prostate Cancer",
                "icon": "🔵",
                "imaging_modality": "MRI Prostate/CT/Bone Scan",
                "key_topics": ["active_surveillance", "radical_prostatectomy", "radiation", "adt", "metastatic_treatment"],
                "specialty": "Urologic Oncology",
                "common_questions": [
                    "What are the criteria for active surveillance?",
                    "Should the patient undergo radical prostatectomy or radiation?",
                    "What is the role of ADT in this case?",
                    "What are the treatment options for metastatic disease?"
                ]
            },
            "pancreatic_cancer": {
                "display_name": "Pancreatic Cancer",
                "icon": "🟡",
                "imaging_modality": "CT Pancreas Protocol",
                "key_topics": ["resectable", "borderline_resectable", "locally_advanced", "metastatic", "adjuvant_therapy"],
                "specialty": "Hepatopancreatobiliary Oncology",
                "common_questions": [
                    "Is the tumor resectable, borderline resectable, or unresectable?",
                    "What is the optimal chemotherapy regimen?",
                    "Should neoadjuvant therapy be considered?",
                    "What is the expected prognosis?"
                ]
            },
            "gastric_cancer": {
                "display_name": "Gastric Cancer",
                "icon": "🟠",
                "imaging_modality": "CT Chest/Abdomen/Pelvis",
                "key_topics": ["perioperative_chemotherapy", "her2_testing", "immunotherapy", "metastatic_treatment"],
                "specialty": "GI Oncology",
                "common_questions": [
                    "What is the role of perioperative chemotherapy?",
                    "Should HER2 testing be performed?",
                    "Is the patient eligible for immunotherapy?",
                    "What is the optimal surgical approach?"
                ]
            },
            "ovarian_cancer": {
                "display_name": "Ovarian Cancer",
                "icon": "🟣",
                "imaging_modality": "CT Abdomen/Pelvis",
                "key_topics": ["cytoreductive_surgery", "platinum_chemotherapy", "parp_inhibitors", "brca_testing"],
                "specialty": "Gynecologic Oncology",
                "common_questions": [
                    "What is the optimal cytoreductive surgery approach?",
                    "Should BRCA testing be performed?",
                    "Is the patient eligible for PARP inhibitor maintenance?",
                    "What is the role of neoadjuvant chemotherapy?"
                ]
            },
            "melanoma": {
                "display_name": "Melanoma",
                "icon": "⚫",
                "imaging_modality": "CT/PET-CT",
                "key_topics": ["surgical_margins", "sentinel_node_biopsy", "adjuvant_immunotherapy", "braf_testing"],
                "specialty": "Surgical Oncology / Medical Oncology",
                "common_questions": [
                    "What are the appropriate surgical margins?",
                    "Should sentinel lymph node biopsy be performed?",
                    "Is adjuvant immunotherapy indicated?",
                    "What is the BRAF mutation status and treatment implications?"
                ]
            },
            "lymphoma": {
                "display_name": "Lymphoma",
                "icon": "🔴",
                "imaging_modality": "PET-CT",
                "key_topics": ["abvd", "r_chop", "radiation", "pet_response", "car_t_therapy"],
                "specialty": "Hematologic Oncology",
                "common_questions": [
                    "What is the lymphoma subtype and stage?",
                    "What is the optimal chemotherapy regimen?",
                    "What is the role of radiation therapy?",
                    "Is the patient eligible for CAR-T therapy?"
                ]
            },
            "leukemia": {
                "display_name": "Leukemia",
                "icon": "🩸",
                "imaging_modality": "Bone Marrow Biopsy/Flow Cytometry",
                "key_topics": ["induction_chemotherapy", "consolidation", "stem_cell_transplant", "targeted_therapy"],
                "specialty": "Hematologic Oncology",
                "common_questions": [
                    "What is the leukemia subtype and risk stratification?",
                    "What is the optimal induction chemotherapy regimen?",
                    "Is the patient a candidate for stem cell transplant?",
                    "Are there targetable mutations (FLT3, IDH, etc.)?"
                ]
            },
            "head_neck_cancer": {
                "display_name": "Head & Neck Cancer",
                "icon": "👤",
                "imaging_modality": "CT/MRI Head & Neck",
                "key_topics": ["hpv_testing", "surgical_resection", "chemoradiation", "immunotherapy"],
                "specialty": "Head & Neck Oncology",
                "common_questions": [
                    "What is the HPV status and its prognostic significance?",
                    "Should the patient undergo surgery or definitive chemoradiation?",
                    "What is the role of immunotherapy?",
                    "What are the expected functional outcomes?"
                ]
            },
            "bladder_cancer": {
                "display_name": "Bladder Cancer",
                "icon": "🔵",
                "imaging_modality": "CT Urogram",
                "key_topics": ["turbt", "bcg_therapy", "radical_cystectomy", "neoadjuvant_chemotherapy", "immunotherapy"],
                "specialty": "Urologic Oncology",
                "common_questions": [
                    "Is this muscle-invasive or non-muscle-invasive bladder cancer?",
                    "What is the role of BCG therapy?",
                    "Should radical cystectomy be performed?",
                    "Is neoadjuvant chemotherapy indicated?"
                ]
            }
        }
    
    def detect_cancer_type(self, case_data):
        """Auto-detect cancer type from case data"""
        cancer_type = case_data.get("cancer_type", "").lower()
        
        # Normalize cancer type
        if "breast" in cancer_type:
            return "breast_cancer"
        elif "lung" in cancer_type or "nsclc" in cancer_type or "sclc" in cancer_type:
            return "lung_cancer"
        elif "colon" in cancer_type or "rectal" in cancer_type or "colorectal" in cancer_type:
            return "colorectal_cancer"
        elif "prostate" in cancer_type:
            return "prostate_cancer"
        elif "pancrea" in cancer_type:
            return "pancreatic_cancer"
        elif "gastric" in cancer_type or "stomach" in cancer_type:
            return "gastric_cancer"
        elif "ovarian" in cancer_type or "ovary" in cancer_type:
            return "ovarian_cancer"
        elif "melanoma" in cancer_type or "skin" in cancer_type:
            return "melanoma"
        elif "lymphoma" in cancer_type or "hodgkin" in cancer_type:
            return "lymphoma"
        elif "leukemia" in cancer_type or "aml" in cancer_type or "all" in cancer_type or "cml" in cancer_type or "cll" in cancer_type:
            return "leukemia"
        elif "head" in cancer_type or "neck" in cancer_type or "oropharyn" in cancer_type:
            return "head_neck_cancer"
        elif "bladder" in cancer_type or "urothelial" in cancer_type:
            return "bladder_cancer"
        else:
            return cancer_type.replace(" ", "_")
    
    def run_complete_pipeline(self, case_file_path, auto_approve=False):
        """
        Run complete MDT pipeline with all features
        
        Args:
            case_file_path: Path to case JSON file
            auto_approve: If True, automatically approve all recommendations
        
        Returns:
            Dict with complete pipeline results
        """
        
        # Load case data
        try:
            with open(case_file_path, 'r') as f:
                case_data = json.load(f)
        except FileNotFoundError:
            print(f"❌ ERROR: Case file not found: {case_file_path}")
            return None
        except json.JSONDecodeError:
            print(f"❌ ERROR: Invalid JSON in case file: {case_file_path}")
            return None
        
        # Detect cancer type
        cancer_type = self.detect_cancer_type(case_data)
        config = self.cancer_configs.get(cancer_type, {
            "display_name": cancer_type.replace("_", " ").title(),
            "icon": "🏥",
            "key_topics": ["treatment", "staging"],
            "specialty": "Medical Oncology",
            "common_questions": []
        })
        
        case_id = case_data.get("patient_id", case_data.get("case_id", "Unknown"))
        
        print("\n" + "="*80)
        print(f"{config['icon']} {config['display_name'].upper()} MDT PIPELINE - COMPLETE SYSTEM")
        print("="*80 + "\n")
        print(f"Case ID: {case_id}")
        print(f"Specialty: {config['specialty']}")
        print(f"Auto-Approve: {'Yes' if auto_approve else 'No'}\n")
        
        pipeline_results = {
            "case_id": case_id,
            "cancer_type": cancer_type,
            "timestamp": datetime.now().isoformat(),
            "hitl_approvals": [],
            "references": [],
            "validation": {},
            "qa_results": []
        }
        
        try:
            # STEP 1: Imaging Analysis
            print("\n" + "="*80)
            print("STEP 1: IMAGING ANALYSIS")
            print("="*80 + "\n")
            
            imaging_result = self.imaging_agent.analyze_imaging(case_data["imaging"])
            pipeline_results["imaging_analysis"] = imaging_result
            
            # HITL Approval for Imaging
            imaging_approval = self.hitl.create_approval_request(
                recommendation_data={
                    "case_id": case_id,
                    "analysis_type": "imaging_analysis",
                    "result": imaging_result
                },
                recommendation_type="imaging_analysis"
            )
            
            if auto_approve:
                print("\n[AUTO-APPROVE MODE: Approving imaging analysis]")
                imaging_approval = self.hitl.approve_request(
                    imaging_approval["request_id"],
                    clinician_id="AUTO_SYSTEM",
                    notes="Auto-approved for demo purposes"
                )
            
            pipeline_results["hitl_approvals"].append({
                "step": "imaging_analysis",
                "request_id": imaging_approval["request_id"],
                "status": imaging_approval["status"]
            })
            
            print(f"\n✅ Imaging Analysis Complete")
            print(f"   HITL Status: {imaging_approval['status'].upper()}")
            
            # STEP 2: Specialist Recommendations
            print("\n" + "="*80)
            print("STEP 2: SPECIALIST RECOMMENDATIONS")
            print("="*80 + "\n")
            
            specialist_result = self.specialist_agent.provide_recommendation(case_data)
            
            # Add references to specialist recommendations
            cited_specialist = self.ref_system.add_citations_to_recommendation(
                recommendation_text=specialist_result,
                cancer_type=cancer_type,
                topics=config["key_topics"]
            )
            
            pipeline_results["specialist_recommendations"] = cited_specialist["recommendation_with_citations"]
            pipeline_results["references"].extend(cited_specialist["references"])
            
            # HITL Approval for Specialist Recommendations
            specialist_approval = self.hitl.create_approval_request(
                recommendation_data={
                    "case_id": case_id,
                    "analysis_type": "specialist_recommendations",
                    "result": cited_specialist["recommendation_with_citations"]
                },
                recommendation_type="specialist_recommendations"
            )
            
            if auto_approve:
                print("\n[AUTO-APPROVE MODE: Approving specialist recommendations]")
                specialist_approval = self.hitl.approve_request(
                    specialist_approval["request_id"],
                    clinician_id="AUTO_SYSTEM",
                    notes="Auto-approved for demo purposes"
                )
            
            pipeline_results["hitl_approvals"].append({
                "step": "specialist_recommendations",
                "request_id": specialist_approval["request_id"],
                "status": specialist_approval["status"]
            })
            
            print(f"\n✅ Specialist Recommendations Complete")
            print(f"   Added {cited_specialist['reference_count']} references")
            print(f"   HITL Status: {specialist_approval['status'].upper()}")
            
            # STEP 3: Validation & Q&A
            print("\n" + "="*80)
            print("STEP 3: VALIDATION & Q&A")
            print("="*80 + "\n")
            
            validation_qa_results = self.validation_qa.validate_and_qa(
                case_data=case_data,
                recommendation={"recommendation": specialist_result},
                questions=config.get("common_questions", [])[:3]  # First 3 questions
            )
            
            pipeline_results["validation"] = validation_qa_results["validation"]
            pipeline_results["qa_results"] = validation_qa_results["qa_results"]
            
            print(f"\n✅ Validation & Q&A Complete")
            print(f"   Validation: {'✅ PASSED' if validation_qa_results['validation']['validation_passed'] else '❌ FAILED'}")
            print(f"   Confidence: {validation_qa_results['validation']['confidence_score']}")
            print(f"   Questions Answered: {len(validation_qa_results['qa_results'])}")
            
            # STEP 4: MDT Brief Generation
            print("\n" + "="*80)
            print("STEP 4: MDT BRIEF GENERATION")
            print("="*80 + "\n")
            
            mdt_brief = self.mdt_brief_agent.generate_mdt_brief(
                case_data=case_data,
                imaging_analysis=imaging_result,
                specialist_recommendations=cited_specialist["recommendation_with_citations"]
            )
            
            pipeline_results["mdt_brief"] = mdt_brief
            
            # HITL Approval for MDT Brief
            brief_approval = self.hitl.create_approval_request(
                recommendation_data={
                    "case_id": case_id,
                    "analysis_type": "mdt_brief",
                    "result": mdt_brief
                },
                recommendation_type="mdt_brief"
            )
            
            if auto_approve:
                print("\n[AUTO-APPROVE MODE: Approving MDT brief]")
                brief_approval = self.hitl.approve_request(
                    brief_approval["request_id"],
                    clinician_id="AUTO_SYSTEM",
                    notes="Auto-approved for demo purposes"
                )
            
            pipeline_results["hitl_approvals"].append({
                "step": "mdt_brief",
                "request_id": brief_approval["request_id"],
                "status": brief_approval["status"]
            })
            
            print(f"\n✅ MDT Brief Complete")
            print(f"   HITL Status: {brief_approval['status'].upper()}")
            
        except Exception as e:
            print(f"\n❌ ERROR in pipeline: {str(e)}")
            import traceback
            traceback.print_exc()
            return None
        
        # Save results
        output_dir = Path(f"outputs/{cancer_type}_complete")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save JSON
        json_file = output_dir / f"complete_results_{case_id}_{timestamp}.json"
        with open(json_file, 'w') as f:
            json.dump(pipeline_results, f, indent=2)
        
        # Save human-readable text
        text_file = output_dir / f"complete_results_{case_id}_{timestamp}.txt"
        with open(text_file, 'w') as f:
            f.write("="*80 + "\n")
            f.write(f"{config['icon']} {config['display_name'].upper()} MDT PIPELINE - COMPLETE RESULTS\n")
            f.write("="*80 + "\n\n")
            f.write(f"Case ID: {case_id}\n")
            f.write(f"Cancer Type: {config['display_name']}\n")
            f.write(f"Specialty: {config['specialty']}\n")
            f.write(f"Timestamp: {pipeline_results['timestamp']}\n\n")
            
            f.write("="*80 + "\n")
            f.write("IMAGING ANALYSIS\n")
            f.write("="*80 + "\n\n")
            f.write(str(pipeline_results["imaging_analysis"]) + "\n\n")
            
            f.write("="*80 + "\n")
            f.write("SPECIALIST RECOMMENDATIONS (WITH REFERENCES)\n")
            f.write("="*80 + "\n\n")
            f.write(pipeline_results["specialist_recommendations"] + "\n\n")
            
            f.write("="*80 + "\n")
            f.write("VALIDATION RESULTS\n")
            f.write("="*80 + "\n\n")
            validation = pipeline_results["validation"]
            f.write(f"Status: {'✅ PASSED' if validation['validation_passed'] else '❌ FAILED'}\n")
            f.write(f"Confidence: {validation['confidence_score']}\n\n")
            
            if validation["errors"]:
                f.write("ERRORS:\n")
                for error in validation["errors"]:
                    f.write(f"  {error}\n")
                f.write("\n")
            
            if validation["warnings"]:
                f.write("WARNINGS:\n")
                for warning in validation["warnings"]:
                    f.write(f"  {warning}\n")
                f.write("\n")
            
            if validation["recommendations"]:
                f.write("RECOMMENDATIONS:\n")
                for rec in validation["recommendations"]:
                    f.write(f"  {rec}\n")
                f.write("\n")
            
            f.write("="*80 + "\n")
            f.write("CLINICAL Q&A\n")
            f.write("="*80 + "\n\n")
            for i, qa in enumerate(pipeline_results["qa_results"], 1):
                f.write(f"Q{i}: {qa['question']}\n\n")
                f.write(f"A{i}: {qa['answer']}\n\n")
                f.write("-"*80 + "\n\n")
            
            f.write("="*80 + "\n")
            f.write("MDT BRIEF\n")
            f.write("="*80 + "\n\n")
            f.write(str(pipeline_results["mdt_brief"]) + "\n\n")
            
            f.write("="*80 + "\n")
            f.write("HITL APPROVAL SUMMARY\n")
            f.write("="*80 + "\n\n")
            for approval in pipeline_results["hitl_approvals"]:
                f.write(f"Step: {approval['step']}\n")
                f.write(f"Request ID: {approval['request_id']}\n")
                f.write(f"Status: {approval['status'].upper()}\n\n")
        
        print("\n" + "="*80)
        print(f"{config['icon']} PIPELINE COMPLETE")
        print("="*80)
        print(f"Results saved to: {output_dir}")
        print(f"  - JSON: {json_file.name}")
        print(f"  - Text: {text_file.name}")
        print(f"\nHITL Approval Summary:")
        for approval in pipeline_results["hitl_approvals"]:
            print(f"  - {approval['step']}: {approval['status'].upper()}")
        print(f"\nValidation: {'✅ PASSED' if pipeline_results['validation']['validation_passed'] else '❌ FAILED'}")
        print(f"Confidence: {pipeline_results['validation']['confidence_score']}")
        print(f"Total References: {len(pipeline_results['references'])}")
        print(f"Questions Answered: {len(pipeline_results['qa_results'])}")
        print("="*80 + "\n")
        
        return pipeline_results


def main():
    """Run complete MDT platform for all available cases"""
    
    platform = CompleteMDTPlatform()
    
    # Define cases to process
    cases = [
        ("data/synthetic_cases/case_001.json", "Breast Cancer"),
        ("data/synthetic_cases/case_002.json", "Lung Cancer"),
        ("data/synthetic_cases/case_003.json", "Colorectal Cancer")
    ]
    
    print("\n" + "="*80)
    print("🏥 RUNNING COMPLETE MDT PLATFORM FOR ALL CASES")
    print("="*80 + "\n")
    
    for case_file, cancer_name in cases:
        try:
            print(f"\n{'='*80}")
            print(f"Processing: {cancer_name}")
            print(f"{'='*80}\n")
            
            results = platform.run_complete_pipeline(
                case_file_path=case_file,
                auto_approve=True
            )
            
            if results:
                print(f"\n✅ {cancer_name} pipeline completed successfully!")
            else:
                print(f"\n❌ {cancer_name} pipeline failed!")
        except FileNotFoundError:
            print(f"\n⚠️ Skipping {cancer_name} - case file not found: {case_file}")
        except Exception as e:
            print(f"\n❌ Error processing {cancer_name}: {str(e)}")
    
    print("\n" + "="*80)
    print("🎉 ALL PIPELINES COMPLETE!")
    print("="*80)
    print("\n📁 Check outputs/*_complete/ directories for results")


if __name__ == "__main__":
    main()

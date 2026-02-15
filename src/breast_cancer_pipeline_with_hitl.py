"""
Breast Cancer MDT Pipeline with HITL Approval
Integrates Human-in-the-Loop approval system into the breast cancer workflow
"""

import json
from pathlib import Path
from image_analysis import ImageAnalyzer
from specialist_advisor import MedicalOncologist
from case_brief_generator import CaseBriefGenerator
from hitl_approval_system import HITLApprovalSystem

def run_breast_cancer_pipeline_with_hitl(case_file_path, auto_approve=False):
    """
    Run complete breast cancer MDT pipeline with HITL approval
    
    Args:
        case_file_path: Path to case JSON file
        auto_approve: If True, automatically approve all recommendations (for testing)
    
    Returns:
        Dict with pipeline results and approval status
    """
    
    print("\n" + "="*80)
    print("BREAST CANCER MDT PIPELINE WITH HITL APPROVAL")
    print("="*80 + "\n")
    
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
    
    case_id = case_data.get("patient_id", case_data.get("case_id", "Unknown"))
    print(f"Processing Case: {case_id}")
    
    # Safe access to patient info
    demographics = case_data.get('demographics', case_data.get('patient_info', {}))
    if demographics:
        print(f"Patient: {demographics.get('age', 'N/A')}yo {demographics.get('sex', demographics.get('gender', 'N/A'))}")
    
    print(f"Cancer Type: {case_data.get('cancer_type', 'N/A')}\n")
    
    # Initialize HITL system
    hitl = HITLApprovalSystem()
    
    # Initialize agents
    imaging_agent = ImageAnalyzer()
    specialist_agent = MedicalOncologist()
    mdt_brief_agent = CaseBriefGenerator()
    
    pipeline_results = {
        "case_id": case_id,
        "imaging_analysis": None,
        "specialist_recommendations": None,
        "mdt_brief": None,
        "hitl_approvals": []
    }
    
    # ===== STEP 1: IMAGING ANALYSIS =====
    print("\n" + "="*80)
    print("STEP 1: IMAGING ANALYSIS")
    print("="*80 + "\n")
    
    try:
        # Pass just the imaging section
        imaging_result = imaging_agent.analyze_imaging(case_data["imaging"])
        pipeline_results["imaging_analysis"] = imaging_result
        
        # Create HITL approval request for imaging analysis
        imaging_approval = hitl.create_approval_request(
            recommendation_data={
                "case_id": case_id,
                "analysis_type": "imaging_analysis",
                "result": imaging_result
            },
            recommendation_type="imaging_analysis"
        )
        
        if auto_approve:
            print("\n[AUTO-APPROVE MODE: Approving imaging analysis]")
            hitl.approve_recommendation(
                request_id=imaging_approval["request_id"],
                clinician_id="AUTO_SYSTEM",
                notes="Auto-approved for demo purposes"
            )
            imaging_approved = True
        else:
            print("\n⏳ Waiting for clinician approval of imaging analysis...")
            imaging_approved = False
        
        pipeline_results["hitl_approvals"].append({
            "step": "imaging_analysis",
            "request_id": imaging_approval["request_id"],
            "status": "approved" if imaging_approved else "pending"
        })
    except Exception as e:
        print(f"❌ ERROR in imaging analysis: {str(e)}")
        import traceback
        traceback.print_exc()
        return pipeline_results
    
    # ===== STEP 2: SPECIALIST RECOMMENDATIONS =====
    print("\n" + "="*80)
    print("STEP 2: SPECIALIST RECOMMENDATIONS")
    print("="*80 + "\n")
    
    try:
        specialist_result = specialist_agent.provide_recommendation(case_data)
        pipeline_results["specialist_recommendations"] = specialist_result
        
        # Create HITL approval request for specialist recommendations
        specialist_approval = hitl.create_approval_request(
            recommendation_data={
                "case_id": case_id,
                "analysis_type": "specialist_recommendations",
                "result": specialist_result
            },
            recommendation_type="specialist_recommendations"
        )
        
        if auto_approve:
            print("\n[AUTO-APPROVE MODE: Approving specialist recommendations]")
            hitl.approve_recommendation(
                request_id=specialist_approval["request_id"],
                clinician_id="AUTO_SYSTEM",
                notes="Auto-approved for demo purposes"
            )
            specialist_approved = True
        else:
            print("\n⏳ Waiting for clinician approval of specialist recommendations...")
            specialist_approved = False
        
        pipeline_results["hitl_approvals"].append({
            "step": "specialist_recommendations",
            "request_id": specialist_approval["request_id"],
            "status": "approved" if specialist_approved else "pending"
        })
    except Exception as e:
        print(f"❌ ERROR in specialist recommendations: {str(e)}")
        import traceback
        traceback.print_exc()
        return pipeline_results
    
    # ===== STEP 3: MDT BRIEF GENERATION =====
    print("\n" + "="*80)
    print("STEP 3: MDT BRIEF GENERATION")
    print("="*80 + "\n")
    
    try:
        mdt_brief_result = mdt_brief_agent.generate_mdt_brief(
            case_data=case_data,
            imaging_analysis=imaging_result,
            specialist_recommendations=specialist_result
        )
        pipeline_results["mdt_brief"] = mdt_brief_result
        
        # Create HITL approval request for MDT brief
        mdt_brief_approval = hitl.create_approval_request(
            recommendation_data={
                "case_id": case_id,
                "analysis_type": "mdt_brief",
                "result": mdt_brief_result
            },
            recommendation_type="mdt_brief"
        )
        
        if auto_approve:
            print("\n[AUTO-APPROVE MODE: Approving MDT brief]")
            hitl.approve_recommendation(
                request_id=mdt_brief_approval["request_id"],
                clinician_id="AUTO_SYSTEM",
                notes="Auto-approved for demo purposes"
            )
            mdt_brief_approved = True
        else:
            print("\n⏳ Waiting for clinician approval of MDT brief...")
            mdt_brief_approved = False
        
        pipeline_results["hitl_approvals"].append({
            "step": "mdt_brief",
            "request_id": mdt_brief_approval["request_id"],
            "status": "approved" if mdt_brief_approved else "pending"
        })
    except Exception as e:
        print(f"❌ ERROR in MDT brief generation: {str(e)}")
        import traceback
        traceback.print_exc()
        return pipeline_results
    
    # ===== SAVE RESULTS =====
    output_dir = Path("outputs/breast_cancer_hitl")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    output_file = output_dir / f"pipeline_results_{case_id}_hitl.json"
    with open(output_file, 'w') as f:
        json.dump(pipeline_results, f, indent=2)
    
    print("\n" + "="*80)
    print("PIPELINE COMPLETE WITH HITL")
    print("="*80)
    print(f"Results saved to: {output_file}")
    print(f"\nHITL Approval Summary:")
    for approval in pipeline_results["hitl_approvals"]:
        print(f"  - {approval['step']}: {approval['status'].upper()}")
        print(f"    Request ID: {approval['request_id']}")
    print("="*80 + "\n")
    
    return pipeline_results


if __name__ == "__main__":
    # Run pipeline with auto-approve for demo
    case_file = "data/synthetic_cases/case_001.json"
    
    print("\n🚀 Running Breast Cancer Pipeline with HITL (Auto-Approve Mode)")
    print("   In production, each step would pause for clinician review\n")
    
    results = run_breast_cancer_pipeline_with_hitl(
        case_file_path=case_file,
        auto_approve=True  # Set to False in production
    )
    
    if results:
        print("\n✅ Pipeline completed successfully!")
        print(f"   Check outputs/breast_cancer_hitl/ for results")
        print(f"   Check outputs/hitl_approvals/ for approval logs")
    else:
        print("\n❌ Pipeline failed. Check errors above.")

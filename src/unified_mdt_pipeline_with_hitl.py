"""
Unified Cancer MDT Pipeline with HITL Approval, References, and RAG Literature Retrieval
Works for all cancer types: Breast, Lung, Colorectal, etc.
"""

import json
import logging
from pathlib import Path
from image_analysis import ImageAnalyzer
from specialist_advisor import MedicalOncologist
from case_brief_generator import CaseBriefGenerator
from hitl_approval_system import HITLApprovalSystem
from reference_system import ReferenceSystem
from rag_pipeline import MedicalRAGPipeline

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


class UnifiedMDTPipeline:
    def __init__(self):
        """Initialize unified MDT pipeline"""
        self.hitl = HITLApprovalSystem()
        self.ref_system = ReferenceSystem()
        self.imaging_agent = ImageAnalyzer()
        self.specialist_agent = MedicalOncologist()
        self.mdt_brief_agent = CaseBriefGenerator()

        # Initialise the RAG pipeline once — models load from cache after first run
        logging.info("Initialising MedicalRAGPipeline...")
        self.rag_pipeline = MedicalRAGPipeline(base_dir=str(Path(__file__).parent.parent))
        logging.info("MedicalRAGPipeline ready.")

        # Cancer-specific configurations
        self.cancer_configs = {
            "breast_cancer": {
                "display_name": "Breast Cancer",
                "icon": "🎗️",
                "imaging_modality": "Mammography/MRI/CT",
                "key_topics": ["neoadjuvant", "adjuvant", "hormonal_therapy", "targeted_therapy"],
                "specialty": "Breast Oncology"
            },
            "lung_cancer": {
                "display_name": "Lung Cancer",
                "icon": "🫁",
                "imaging_modality": "CT Chest",
                "key_topics": ["immunotherapy", "targeted_therapy", "chemoradiation", "molecular_testing"],
                "specialty": "Thoracic Oncology"
            },
            "colorectal_cancer": {
                "display_name": "Colorectal Cancer",
                "icon": "🎗️",
                "imaging_modality": "CT Abdomen/Pelvis",
                "key_topics": ["adjuvant_therapy", "metastatic_treatment", "molecular_testing"],
                "specialty": "GI Oncology"
            }
        }

    def detect_cancer_type(self, case_data):
        """Auto-detect cancer type from case data"""
        cancer_type = case_data.get("cancer_type", "").lower().replace(" ", "_")

        if "breast" in cancer_type:
            return "breast_cancer"
        elif "lung" in cancer_type or "nsclc" in cancer_type or "sclc" in cancer_type:
            return "lung_cancer"
        elif "colon" in cancer_type or "rectal" in cancer_type or "colorectal" in cancer_type:
            return "colorectal_cancer"
        else:
            return cancer_type

    def _build_rag_query(self, case_data, cancer_type):
        """Build a focused clinical query from case data for RAG retrieval"""
        parts = []

        # Cancer type
        parts.append(cancer_type.replace("_", " "))

        # Molecular markers
        molecular = case_data.get("molecular_profile", case_data.get("biomarkers", {}))
        if molecular:
            for key, val in molecular.items():
                if val and str(val).lower() not in ("unknown", "n/a", "none", ""):
                    parts.append(f"{key} {val}")

        # Stage
        stage = case_data.get("stage", case_data.get("clinical_stage", ""))
        if stage:
            parts.append(f"stage {stage}")

        # Primary treatment intent
        intent = case_data.get("treatment_intent", case_data.get("intent", ""))
        if intent:
            parts.append(intent)

        # Fallback: use diagnosis field
        if len(parts) <= 1:
            diagnosis = case_data.get("diagnosis", case_data.get("primary_diagnosis", ""))
            if diagnosis:
                parts.append(diagnosis)

        query = " ".join(parts)
        logging.info(f"Built RAG query: '{query}'")
        return query

    def run_pipeline(self, case_file_path, auto_approve=False):
        """
        Run complete MDT pipeline with HITL approval, references, and RAG literature retrieval.

        Args:
            case_file_path: Path to case JSON file
            auto_approve: If True, automatically approve all recommendations

        Returns:
            Dict with pipeline results and approval status
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
            "imaging_modality": "Medical Imaging",
            "key_topics": ["treatment", "staging"],
            "specialty": "Medical Oncology"
        })

        case_id = case_data.get("patient_id", case_data.get("case_id", "Unknown"))

        print("\n" + "="*80)
        print(f"{config['icon']} {config['display_name'].upper()} MDT PIPELINE WITH HITL, REFERENCES & RAG")
        print("="*80 + "\n")
        print(f"Processing Case: {case_id}")

        patient_info = case_data.get('patient_info', case_data.get('demographics', {}))
        if patient_info:
            print(f"Patient: {patient_info.get('age', 'N/A')}yo {patient_info.get('gender', patient_info.get('sex', 'N/A'))}")

        print(f"Cancer Type: {config['display_name']}")
        print(f"Specialty: {config['specialty']}\n")

        pipeline_results = {
            "case_id": case_id,
            "cancer_type": cancer_type,
            "imaging_analysis": None,
            "specialist_recommendations": None,
            "mdt_brief": None,
            "hitl_approvals": [],
            "references": [],
            "rag_literature": []
        }

        # ===== STEP 1: IMAGING ANALYSIS =====
        print("\n" + "="*80)
        print(f"STEP 1: IMAGING ANALYSIS ({config['imaging_modality']})")
        print("="*80 + "\n")

        try:
            imaging_result = self.imaging_agent.analyze_imaging(case_data["imaging"])
            pipeline_results["imaging_analysis"] = imaging_result

            print(f"✅ Imaging Analysis Complete")

            imaging_refs = self.ref_system.get_references_for_topic(cancer_type, "staging")
            pipeline_results["references"].extend(imaging_refs)

            imaging_approval = self.hitl.create_approval_request(
                recommendation_data={
                    "case_id": case_id,
                    "cancer_type": cancer_type,
                    "analysis_type": "imaging_analysis",
                    "result": imaging_result,
                    "references": imaging_refs
                },
                recommendation_type=f"{cancer_type}_imaging_analysis"
            )

            if auto_approve:
                print("\n[AUTO-APPROVE MODE: Approving imaging analysis]")
                self.hitl.create_approval_request(
                    request_id=imaging_approval["request_id"],
                    clinician_id="AUTO_SYSTEM",
                    notes="Auto-approved for demo purposes"
                )
                imaging_approved = True
            else:
                print("\n⏳ Waiting for clinician approval...")
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

        # ===== STEP 2: RAG LITERATURE RETRIEVAL =====
        print("\n" + "="*80)
        print("STEP 2: RAG LITERATURE RETRIEVAL (Guidelines + Live PubMed)")
        print("="*80 + "\n")

        rag_query = self._build_rag_query(case_data, cancer_type)
        try:
            rag_results = self.rag_pipeline.retrieve(
                query=rag_query,
                cancer_type=cancer_type,
                top_k=10
            )
            pipeline_results["rag_literature"] = rag_results

            print(f"✅ RAG Retrieval Complete — {len(rag_results)} references retrieved")
            print(f"   Query used: '{rag_query}'")
            for i, ref in enumerate(rag_results[:5]):
                # Handle both flat and nested metadata formats
                if 'metadata' in ref:
                    title = ref['metadata'].get('title', 'N/A')
                    source = ref['metadata'].get('source', 'N/A')
                else:
                    title = ref.get('title', 'N/A')
                    source = ref.get('source', 'N/A')
                print(f"   {i+1}. {title[:80]}  ({source})")

        except Exception as e:
            print(f"⚠️  RAG retrieval failed (non-fatal): {str(e)} — continuing without live literature")
            rag_results = []

        # ===== STEP 3: SPECIALIST RECOMMENDATIONS =====
        print("\n" + "="*80)
        print(f"STEP 3: SPECIALIST RECOMMENDATIONS ({config['specialty']})")
        print("="*80 + "\n")

        try:
            specialist_result = self.specialist_agent.provide_recommendation(case_data)
            pipeline_results["specialist_recommendations"] = specialist_result

            print(f"✅ Specialist Recommendations Complete")

            recommendation_text = specialist_result.get('recommendation', '')
            cited_recommendation = self.ref_system.add_citations_to_recommendation(
                recommendation_text=recommendation_text,
                cancer_type=cancer_type,
                topics=config['key_topics']
            )

            specialist_result['recommendation_with_citations'] = cited_recommendation['recommendation_with_citations']
            specialist_result['references'] = cited_recommendation['references']
            pipeline_results["references"].extend(cited_recommendation['references'])

            # Attach RAG literature to specialist result for downstream use
            specialist_result['rag_literature'] = rag_results

            print(f"   Added {cited_recommendation['reference_count']} static references")
            print(f"   Attached {len(rag_results)} RAG literature results")

            specialist_approval = self.hitl.create_approval_request(
                recommendation_data={
                    "case_id": case_id,
                    "cancer_type": cancer_type,
                    "analysis_type": "specialist_recommendations",
                    "result": specialist_result
                },
                recommendation_type=f"{cancer_type}_specialist_recommendations"
            )

            if auto_approve:
                print("\n[AUTO-APPROVE MODE: Approving specialist recommendations]")
                self.hitl.create_approval_request(
                    request_id=specialist_approval["request_id"],
                    clinician_id="AUTO_SYSTEM",
                    notes="Auto-approved for demo purposes"
                )
                specialist_approved = True
            else:
                print("\n⏳ Waiting for clinician approval...")
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

        # ===== STEP 4: MDT BRIEF GENERATION =====
        print("\n" + "="*80)
        print("STEP 4: MDT BRIEF GENERATION")
        print("="*80 + "\n")

        try:
            mdt_brief_result = self.mdt_brief_agent.generate_mdt_brief(
                case_data=case_data,
                imaging_analysis=imaging_result,
                specialist_recommendations=specialist_result
            )
            pipeline_results["mdt_brief"] = mdt_brief_result

            print(f"✅ MDT Brief Generated")

            mdt_brief_approval = self.hitl.create_approval_request(
                recommendation_data={
                    "case_id": case_id,
                    "cancer_type": cancer_type,
                    "analysis_type": "mdt_brief",
                    "result": mdt_brief_result
                },
                recommendation_type=f"{cancer_type}_mdt_brief"
            )

            if auto_approve:
                print("\n[AUTO-APPROVE MODE: Approving MDT brief]")
                self.hitl.create_approval_request(
                    request_id=mdt_brief_approval["request_id"],
                    clinician_id="AUTO_SYSTEM",
                    notes="Auto-approved for demo purposes"
                )
                mdt_brief_approved = True
            else:
                print("\n⏳ Waiting for clinician approval...")
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
        self._save_results(pipeline_results, case_data, config)

        return pipeline_results

    def _save_results(self, pipeline_results, case_data, config):
        """Save pipeline results with citations and RAG literature"""

        case_id = pipeline_results["case_id"]
        cancer_type = pipeline_results["cancer_type"]

        output_dir = Path(f"outputs/{cancer_type}_hitl")
        output_dir.mkdir(parents=True, exist_ok=True)

        # Save JSON
        output_file = output_dir / f"pipeline_results_{case_id}_hitl_cited.json"
        with open(output_file, 'w') as f:
            json.dump(pipeline_results, f, indent=2, default=str)

        # Save human-readable text
        text_output_file = output_dir / f"pipeline_results_{case_id}_hitl_cited.txt"
        with open(text_output_file, 'w') as f:
            f.write("="*80 + "\n")
            f.write(f"{config['display_name'].upper()} MDT PIPELINE RESULTS WITH CITATIONS & RAG LITERATURE\n")
            f.write("="*80 + "\n\n")
            f.write(f"Case ID: {case_id}\n")
            f.write(f"Cancer Type: {config['display_name']}\n\n")

            f.write("-"*80 + "\n")
            f.write("IMAGING ANALYSIS\n")
            f.write("-"*80 + "\n")
            f.write(pipeline_results["imaging_analysis"].get('ai_analysis', 'N/A') + "\n\n")

            f.write("-"*80 + "\n")
            f.write("SPECIALIST RECOMMENDATIONS WITH CITATIONS\n")
            f.write("-"*80 + "\n")
            f.write(pipeline_results["specialist_recommendations"].get('recommendation_with_citations', 'N/A') + "\n\n")

            f.write("-"*80 + "\n")
            f.write("MDT BRIEF\n")
            f.write("-"*80 + "\n")
            f.write(pipeline_results["mdt_brief"].get('brief_content', 'N/A') + "\n\n")

            # Write RAG literature section
            f.write("="*80 + "\n")
            f.write("RETRIEVED LITERATURE (RAG — Guidelines + Live PubMed)\n")
            f.write("="*80 + "\n")
            rag_lit = pipeline_results.get("rag_literature", [])
            if rag_lit:
                for i, ref in enumerate(rag_lit):
                    if 'metadata' in ref:
                        title  = ref['metadata'].get('title', 'N/A')
                        source = ref['metadata'].get('source', 'N/A')
                        url    = ref['metadata'].get('url', 'N/A')
                    else:
                        title  = ref.get('title', 'N/A')
                        source = ref.get('source', 'N/A')
                        url    = ref.get('url', 'N/A')
                    f.write(f"\n{i+1}. {title}\n")
                    f.write(f"   Source: {source}\n")
                    f.write(f"   URL: {url}\n")
            else:
                f.write("No RAG literature retrieved.\n")

            f.write("\n" + "="*80 + "\n")
            f.write("HITL APPROVAL STATUS\n")
            f.write("="*80 + "\n")
            for approval in pipeline_results["hitl_approvals"]:
                f.write(f"\n{approval['step']}: {approval['status'].upper()}\n")
                f.write(f"Request ID: {approval['request_id']}\n")

        print("\n" + "="*80)
        print(f"{config['icon']} PIPELINE COMPLETE WITH HITL, REFERENCES & RAG LITERATURE")
        print("="*80)
        print(f"Results saved to:")
        print(f"  JSON: {output_file}")
        print(f"  Text: {text_output_file}")
        print(f"\nHITL Approval Summary:")
        for approval in pipeline_results["hitl_approvals"]:
            print(f"  - {approval['step']}: {approval['status'].upper()}")
            print(f"    Request ID: {approval['request_id']}")
        print(f"\nTotal Static References: {len(pipeline_results['references'])}")
        print(f"Total RAG Literature: {len(pipeline_results.get('rag_literature', []))}")
        print("="*80 + "\n")


def main():
    """Run unified MDT pipeline for multiple cancer types"""

    pipeline = UnifiedMDTPipeline()

    test_cases = [
        ("data/synthetic_cases/case_001.json", "Breast Cancer"),
        ("data/synthetic_cases/case_002.json", "Lung Cancer"),
        ("data/synthetic_cases/case_003.json", "Colorectal Cancer")
    ]

    print("\n" + "="*80)
    print("🏥 UNIFIED CANCER MDT PIPELINE")
    print("   Testing multiple cancer types with HITL, References & RAG")
    print("="*80)

    for case_file, cancer_name in test_cases:
        print(f"\n\n{'='*80}")
        print(f"Processing {cancer_name} Case")
        print(f"{'='*80}\n")

        try:
            results = pipeline.run_pipeline(
                case_file_path=case_file,
                auto_approve=True
            )

            if results:
                print(f"\n✅ {cancer_name} pipeline completed successfully!")
                print(f"   RAG Literature retrieved: {len(results.get('rag_literature', []))}")
            else:
                print(f"\n❌ {cancer_name} pipeline failed!")
        except FileNotFoundError:
            print(f"\n⚠️ Skipping {cancer_name} - case file not found: {case_file}")
        except Exception as e:
            print(f"\n❌ Error processing {cancer_name}: {str(e)}")


if __name__ == "__main__":
    main()

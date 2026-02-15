"""
Unified Validation & Q&A System
Combines anti-hallucination validation with clinical Q&A for all cancer types
"""

import json
from pathlib import Path
from datetime import datetime
import re
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch

class AntiHallucinationValidator:
    """Validates AI recommendations against clinical guidelines"""
    
    def __init__(self):
        self.output_dir = Path("outputs/validation")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.validation_rules = self._load_validation_rules()
        self.confidence_thresholds = {"high": 0.85, "medium": 0.65, "low": 0.45}
    
    def _load_validation_rules(self):
        """Load clinical validation rules for all cancer types"""
        return {
            "breast_cancer": {
                "staging": {
                    "valid_stages": ["Stage 0", "Stage I", "Stage IA", "Stage IB", 
                                   "Stage II", "Stage IIA", "Stage IIB",
                                   "Stage III", "Stage IIIA", "Stage IIIB", "Stage IIIC",
                                   "Stage IV"],
                    "tnm_pattern": r"T[0-4][a-c]?N[0-3][a-c]?M[0-1][a-c]?"
                },
                "receptors": {
                    "required": ["ER", "PR", "HER2"],
                    "valid_values": {
                        "ER": ["Positive", "Negative", "positive", "negative"],
                        "PR": ["Positive", "Negative", "positive", "negative"],
                        "HER2": ["Positive", "Negative", "Equivocal", "positive", "negative", "equivocal"]
                    }
                },
                "treatment_contraindications": {
                    "HER2_negative": ["trastuzumab", "pertuzumab", "T-DM1", "trastuzumab emtansine"],
                    "ER_PR_negative": ["tamoxifen", "aromatase inhibitor", "letrozole", "anastrozole", "exemestane"]
                },
                "treatment_requirements": {
                    "HER2_positive": ["trastuzumab", "pertuzumab", "anti-HER2 therapy", "HER2-targeted"],
                    "ER_PR_positive": ["hormonal therapy", "endocrine therapy", "tamoxifen", "aromatase inhibitor"]
                }
            },
            "lung_cancer": {
                "staging": {
                    "valid_stages": ["Stage I", "Stage IA", "Stage IB",
                                   "Stage II", "Stage IIA", "Stage IIB",
                                   "Stage III", "Stage IIIA", "Stage IIIB", "Stage IIIC",
                                   "Stage IV", "Stage IVA", "Stage IVB"],
                    "tnm_pattern": r"T[0-4][a-c]?N[0-3]M[0-1][a-c]?"
                },
                "molecular_testing": {
                    "required": ["EGFR", "ALK", "ROS1", "PD-L1"],
                    "driver_mutations": ["EGFR", "ALK", "ROS1", "BRAF", "KRAS", "MET", "RET", "NTRK"]
                },
                "treatment_contraindications": {
                    "EGFR_negative": ["osimertinib", "erlotinib", "gefitinib", "afatinib"],
                    "ALK_negative": ["alectinib", "crizotinib", "brigatinib", "lorlatinib"],
                    "low_pdl1": ["pembrolizumab monotherapy"]
                },
                "treatment_requirements": {
                    "EGFR_positive": ["EGFR TKI", "osimertinib", "targeted therapy", "tyrosine kinase inhibitor"],
                    "ALK_positive": ["ALK inhibitor", "alectinib", "targeted therapy"]
                }
            },
            "colorectal_cancer": {
                "staging": {
                    "valid_stages": ["Stage 0", "Stage I", "Stage II", "Stage IIA", "Stage IIB", "Stage IIC",
                                   "Stage III", "Stage IIIA", "Stage IIIB", "Stage IIIC",
                                   "Stage IV", "Stage IVA", "Stage IVB", "Stage IVC"],
                    "tnm_pattern": r"T[0-4][a-d]?N[0-2][a-c]?M[0-1][a-c]?"
                },
                "molecular_testing": {
                    "required": ["MSI", "KRAS", "NRAS", "BRAF"],
                    "biomarkers": ["MSI-H", "MSS", "dMMR", "pMMR"]
                },
                "treatment_contraindications": {
                    "RAS_mutant": ["cetuximab", "panitumumab", "anti-EGFR therapy"],
                    "BRAF_V600E": ["anti-EGFR monotherapy"]
                },
                "treatment_requirements": {
                    "MSI_H": ["immunotherapy", "pembrolizumab", "nivolumab"],
                    "RAS_wild_type": ["anti-EGFR therapy", "cetuximab", "panitumumab"]
                }
            },
            "prostate_cancer": {
                "staging": {
                    "valid_stages": ["Stage I", "Stage II", "Stage IIA", "Stage IIB", "Stage IIC",
                                   "Stage III", "Stage IIIA", "Stage IIIB", "Stage IIIC",
                                   "Stage IV", "Stage IVA", "Stage IVB"],
                    "tnm_pattern": r"T[1-4][a-c]?N[0-1]M[0-1][a-c]?"
                },
                "biomarkers": {
                    "required": ["PSA", "Gleason_score"],
                    "risk_groups": ["very_low", "low", "intermediate", "high", "very_high"]
                },
                "treatment_requirements": {
                    "high_risk": ["adt", "radiation", "consideration_of_systemic_therapy"],
                    "metastatic": ["adt", "novel_hormonal_agents"]
                }
            },
            "pancreatic_cancer": {
                "staging": {
                    "valid_stages": ["Stage 0", "Stage IA", "Stage IB", "Stage IIA", "Stage IIB",
                                   "Stage III", "Stage IV"],
                    "tnm_pattern": r"T[0-4]N[0-2]M[0-1]"
                },
                "resectability": {
                    "categories": ["resectable", "borderline_resectable", "locally_advanced", "metastatic"]
                },
                "treatment_requirements": {
                    "resectable": ["surgical_resection", "adjuvant_chemotherapy"],
                    "metastatic": ["systemic_chemotherapy", "folfirinox_or_gemcitabine"]
                }
            },
            "gastric_cancer": {
                "staging": {
                    "valid_stages": ["Stage 0", "Stage IA", "Stage IB", "Stage IIA", "Stage IIB",
                                   "Stage III", "Stage IIIA", "Stage IIIB", "Stage IIIC", "Stage IV"],
                    "tnm_pattern": r"T[0-4][a-b]?N[0-3][a-b]?M[0-1]"
                },
                "biomarkers": {
                    "required": ["HER2", "MSI", "PD-L1"]
                },
                "treatment_requirements": {
                    "HER2_positive": ["trastuzumab"],
                    "MSI_H": ["immunotherapy"]
                }
            },
            "ovarian_cancer": {
                "staging": {
                    "valid_stages": ["Stage I", "Stage IA", "Stage IB", "Stage IC",
                                   "Stage II", "Stage IIA", "Stage IIB",
                                   "Stage III", "Stage IIIA", "Stage IIIB", "Stage IIIC",
                                   "Stage IV", "Stage IVA", "Stage IVB"],
                    "tnm_pattern": r"T[1-3][a-c]?N[0-1]M[0-1][a-b]?"
                },
                "biomarkers": {
                    "required": ["BRCA1", "BRCA2", "HRD"],
                    "tumor_markers": ["CA-125"]
                },
                "treatment_requirements": {
                    "BRCA_mutant": ["parp_inhibitor", "olaparib", "niraparib"],
                    "platinum_sensitive": ["platinum_based_chemotherapy"]
                }
            },
            "melanoma": {
                "staging": {
                    "valid_stages": ["Stage 0", "Stage IA", "Stage IB", "Stage IIA", "Stage IIB", "Stage IIC",
                                   "Stage III", "Stage IIIA", "Stage IIIB", "Stage IIIC", "Stage IIID",
                                   "Stage IV"],
                    "tnm_pattern": r"T[0-4][a-b]?N[0-3][a-c]?M[0-1][a-d]?"
                },
                "biomarkers": {
                    "required": ["BRAF", "PD-L1"],
                    "driver_mutations": ["BRAF_V600E", "BRAF_V600K", "NRAS", "KIT"]
                },
                "treatment_requirements": {
                    "BRAF_V600_mutant": ["braf_inhibitor", "dabrafenib", "vemurafenib", "mek_inhibitor"],
                    "stage_III_IV": ["immunotherapy", "pembrolizumab", "nivolumab"]
                },
                "treatment_contraindications": {
                    "BRAF_wild_type": ["braf_inhibitor", "dabrafenib", "vemurafenib"]
                }
            },
            "lymphoma": {
                "staging": {
                    "valid_stages": ["Stage I", "Stage II", "Stage III", "Stage IV"],
                    "ann_arbor": True
                },
                "subtypes": {
                    "hodgkin": ["classical_hl", "nodular_lymphocyte_predominant"],
                    "non_hodgkin": ["dlbcl", "follicular", "mantle_cell", "burkitt"]
                },
                "treatment_requirements": {
                    "dlbcl": ["r_chop", "rituximab", "chemotherapy"],
                    "hodgkin": ["abvd", "chemotherapy"]
                }
            },
            "leukemia": {
                "subtypes": {
                    "acute": ["aml", "all"],
                    "chronic": ["cml", "cll"]
                },
                "biomarkers": {
                    "aml": ["FLT3", "NPM1", "CEBPA", "IDH1", "IDH2"],
                    "cll": ["del17p", "TP53", "IGHV"]
                },
                "treatment_requirements": {
                    "FLT3_mutant_aml": ["flt3_inhibitor", "midostaurin", "gilteritinib"],
                    "cll": ["btk_inhibitor", "ibrutinib", "acalabrutinib"]
                }
            },
            "head_neck_cancer": {
                "staging": {
                    "valid_stages": ["Stage 0", "Stage I", "Stage II", "Stage III", "Stage IVA", "Stage IVB", "Stage IVC"],
                    "tnm_pattern": r"T[0-4][a-b]?N[0-3][a-c]?M[0-1]"
                },
                "biomarkers": {
                    "required": ["HPV", "PD-L1"],
                    "hpv_status": ["positive", "negative"]
                },
                "treatment_requirements": {
                    "locally_advanced": ["chemoradiation", "cisplatin"],
                    "recurrent_metastatic": ["immunotherapy", "pembrolizumab"]
                }
            },
            "bladder_cancer": {
                "staging": {
                    "valid_stages": ["Stage 0a", "Stage 0is", "Stage I", "Stage II",
                                   "Stage IIIA", "Stage IIIB", "Stage IVA", "Stage IVB"],
                    "tnm_pattern": r"T[a-4][a-b]?N[0-3]M[0-1][a-b]?"
                },
                "muscle_invasion": {
                    "categories": ["nmibc", "mibc"],
                    "nmibc": ["non_muscle_invasive"],
                    "mibc": ["muscle_invasive"]
                },
                "treatment_requirements": {
                    "nmibc_high_risk": ["bcg_therapy", "intravesical_therapy"],
                    "mibc": ["radical_cystectomy", "neoadjuvant_chemotherapy"],
                    "metastatic": ["platinum_based_chemotherapy", "immunotherapy"]
                }
            }
        }
    
    def validate_recommendation(self, case_data, recommendation, cancer_type):
        """Validate AI recommendation against clinical guidelines"""
        
        validation_result = {
            "case_id": case_data.get("patient_id", case_data.get("case_id", "Unknown")),
            "cancer_type": cancer_type,
            "timestamp": datetime.now().isoformat(),
            "validation_passed": True,
            "confidence_score": 1.0,
            "flags": [],
            "warnings": [],
            "errors": [],
            "recommendations": []
        }
        
        cancer_type_normalized = cancer_type.lower().replace(" ", "_")
        
        if cancer_type_normalized not in self.validation_rules:
            validation_result["warnings"].append(f"No validation rules for {cancer_type}")
            validation_result["confidence_score"] = 0.7
            return validation_result
        
        rules = self.validation_rules[cancer_type_normalized]
        
        # Validate staging
        staging_validation = self._validate_staging(case_data, rules)
        validation_result["warnings"].extend(staging_validation["warnings"])
        
        # Validate biomarkers
        biomarker_validation = self._validate_biomarkers(case_data, rules, cancer_type_normalized)
        validation_result["warnings"].extend(biomarker_validation["warnings"])
        
        # Validate treatment
        treatment_validation = self._validate_treatment(case_data, recommendation, rules, cancer_type_normalized)
        validation_result["errors"].extend(treatment_validation["errors"])
        validation_result["warnings"].extend(treatment_validation["warnings"])
        validation_result["recommendations"].extend(treatment_validation["recommendations"])
        
        # Calculate confidence
        validation_result["confidence_score"] = self._calculate_confidence(validation_result)
        validation_result["validation_passed"] = len(validation_result["errors"]) == 0
        
        return validation_result
    
    def _validate_staging(self, case_data, rules):
        """Validate staging information"""
        result = {"warnings": []}
        staging = case_data.get("staging", case_data.get("diagnosis", {}))
        stage = staging.get("stage", "")
        
        if stage and stage not in rules["staging"]["valid_stages"]:
            result["warnings"].append(f"⚠️ Unusual stage format: {stage}")
        
        return result
    
    def _validate_biomarkers(self, case_data, rules, cancer_type):
        """Validate biomarker/receptor status"""
        result = {"warnings": []}
        
        if cancer_type == "breast_cancer":
            pathology = case_data.get("pathology", {})
            receptors = pathology.get("receptors", {})
            
            for required in rules["receptors"]["required"]:
                if required not in receptors:
                    result["warnings"].append(f"⚠️ Missing {required} receptor status")
        
        elif cancer_type == "lung_cancer":
            molecular = case_data.get("molecular_testing", {})
            for required in rules["molecular_testing"]["required"]:
                if required not in molecular and required.lower() not in str(molecular).lower():
                    result["warnings"].append(f"⚠️ Missing {required} molecular testing")
        
        elif cancer_type == "colorectal_cancer":
            molecular = case_data.get("molecular_testing", {})
            for required in rules["molecular_testing"]["required"]:
                if required not in molecular and required.lower() not in str(molecular).lower():
                    result["warnings"].append(f"⚠️ Missing {required} molecular testing")
        
        return result
    
    def _validate_treatment(self, case_data, recommendation, rules, cancer_type):
        """Validate treatment recommendations"""
        result = {"errors": [], "warnings": [], "recommendations": []}
        recommendation_text = recommendation.get("recommendation", "").lower()
        
        if cancer_type == "breast_cancer":
            pathology = case_data.get("pathology", {})
            receptors = pathology.get("receptors", {})
            her2 = receptors.get("HER2", "").lower()
            er = receptors.get("ER", "").lower()
            pr = receptors.get("PR", "").lower()
            
            if "negative" in her2:
                for drug in rules["treatment_contraindications"]["HER2_negative"]:
                    if drug.lower() in recommendation_text:
                        result["errors"].append(f"❌ CONTRAINDICATION: {drug} for HER2-negative patient")
            
            if "negative" in er and "negative" in pr:
                for drug in rules["treatment_contraindications"]["ER_PR_negative"]:
                    if drug.lower() in recommendation_text:
                        result["errors"].append(f"❌ CONTRAINDICATION: {drug} for ER-/PR- patient")
            
            if "positive" in her2:
                has_her2 = any(d.lower() in recommendation_text for d in rules["treatment_requirements"]["HER2_positive"])
                if not has_her2:
                    result["warnings"].append("⚠️ Consider anti-HER2 therapy for HER2+ patient")
                    result["recommendations"].append("✓ Add trastuzumab/pertuzumab for HER2+ disease")
            
            if "positive" in er or "positive" in pr:
                has_hormonal = any(t in recommendation_text for t in rules["treatment_requirements"]["ER_PR_positive"])
                if not has_hormonal:
                    result["warnings"].append("⚠️ Consider hormonal therapy for ER+/PR+ patient")
                    result["recommendations"].append("✓ Add endocrine therapy (tamoxifen/AI)")
        
        elif cancer_type == "lung_cancer":
            molecular = case_data.get("molecular_testing", {})
            driver_mutations = molecular.get("driver_mutations", [])
            
            if any("egfr" in str(m).lower() for m in driver_mutations):
                has_egfr_tki = any(d.lower() in recommendation_text for d in rules["treatment_requirements"]["EGFR_positive"])
                if not has_egfr_tki:
                    result["warnings"].append("⚠️ Consider EGFR TKI for EGFR-mutant patient")
                    result["recommendations"].append("✓ Add osimertinib or EGFR TKI")
            
            if any("alk" in str(m).lower() for m in driver_mutations):
                has_alk = any(d.lower() in recommendation_text for d in rules["treatment_requirements"]["ALK_positive"])
                if not has_alk:
                    result["warnings"].append("⚠️ Consider ALK inhibitor for ALK+ patient")
                    result["recommendations"].append("✓ Add alectinib or ALK inhibitor")
        
        elif cancer_type == "colorectal_cancer":
            molecular = case_data.get("molecular_testing", {})
            kras = str(molecular.get("KRAS", "")).lower()
            nras = str(molecular.get("NRAS", "")).lower()
            
            if "mutant" in kras or "mutant" in nras:
                for drug in rules["treatment_contraindications"]["RAS_mutant"]:
                    if drug.lower() in recommendation_text:
                        result["errors"].append(f"❌ CONTRAINDICATION: {drug} ineffective in RAS-mutant CRC")
        
        return result
    
    def _calculate_confidence(self, validation_result):
        """Calculate confidence score"""
        base = 1.0
        error_penalty = len(validation_result["errors"]) * 0.3
        warning_penalty = len(validation_result["warnings"]) * 0.1
        return max(0.0, round(base - error_penalty - warning_penalty, 2))
    
    def get_confidence_level(self, score):
        """Get confidence level"""
        if score >= self.confidence_thresholds["high"]:
            return "HIGH"
        elif score >= self.confidence_thresholds["medium"]:
            return "MEDIUM"
        elif score >= self.confidence_thresholds["low"]:
            return "LOW"
        return "VERY LOW"


class ClinicalQASystem:
    """Clinical Q&A system for cancer cases"""
    
    def __init__(self, reference_system=None):
        print("Loading MedGemma model for Q&A...")
        self.model_name = "google/medgemma-4b-it"
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        self.model = AutoModelForCausalLM.from_pretrained(
            self.model_name,
            torch_dtype=torch.float32,
            low_cpu_mem_usage=True
        )
        print("MedGemma Q&A model loaded!")
        
        self.output_dir = Path("outputs/qa")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Reference system for citations
        self.reference_system = reference_system
    
    def answer_question(self, question, case_data, context=None, add_references=True):
        """Answer clinical question about a case with references"""
        
        case_id = case_data.get("patient_id", case_data.get("case_id", "Unknown"))
        cancer_type = case_data.get("cancer_type", "Unknown")
        
        # Build context
        patient_info = case_data.get("patient_info", case_data.get("demographics", {}))
        staging = case_data.get("staging", case_data.get("diagnosis", {}))
        
        prompt = f"""You are a clinical oncologist answering questions about a cancer case.

CASE INFORMATION:
- Case ID: {case_id}
- Cancer Type: {cancer_type}
- Patient: {patient_info.get('age', 'N/A')} years old, {patient_info.get('gender', patient_info.get('sex', 'N/A'))}
- Stage: {staging.get('stage', 'N/A')}

"""
        
        # Add additional context if provided
        if context:
            prompt += f"ADDITIONAL CONTEXT:\n{context}\n\n"
        
        prompt += f"""QUESTION:
{question}

Please provide a clear, evidence-based answer:

ANSWER:"""
        
        # Generate answer
        inputs = self.tokenizer(prompt, return_tensors="pt")
        outputs = self.model.generate(
            **inputs,
            max_new_tokens=300,
            temperature=0.7,
            do_sample=True
        )
        
        response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        # Extract answer
        if "ANSWER:" in response:
            answer = response.split("ANSWER:")[-1].strip()
        else:
            answer = response
        
        # Add references if available
        references = []
        reference_text = ""
        
        if add_references and self.reference_system:
            # Extract topics from question
            topics = self._extract_topics_from_question(question, cancer_type)
            
            # Get relevant references
            cancer_type_normalized = cancer_type.lower().replace(" ", "_")
            for topic in topics:
                refs = self.reference_system.get_references_for_topic(cancer_type_normalized, topic)
                references.extend(refs)
            
            # Remove duplicates
            unique_refs = []
            seen_ids = set()
            for ref in references:
                if ref['id'] not in seen_ids:
                    unique_refs.append(ref)
                    seen_ids.add(ref['id'])
            
            # Build reference text
            if unique_refs:
                reference_text = "\n\nREFERENCES:\n"
                for i, ref in enumerate(unique_refs, 1):
                    reference_text += f"[{i}] {ref['title']}"
                    if 'organization' in ref:
                        reference_text += f" ({ref['organization']})"
                    elif 'journal' in ref:
                        reference_text += f" ({ref['journal']}, {ref.get('year', '')})"
                    reference_text += "\n"
        
        qa_result = {
            "case_id": case_id,
            "cancer_type": cancer_type,
            "question": question,
            "answer": answer + reference_text,
            "references": references,
            "timestamp": datetime.now().isoformat()
        }
        
        return qa_result
    
    def _extract_topics_from_question(self, question, cancer_type):
        """Extract relevant topics from question"""
        question_lower = question.lower()
        
        # Common topic keywords
        topic_keywords = {
            "neoadjuvant": ["neoadjuvant", "preoperative"],
            "adjuvant": ["adjuvant", "postoperative"],
            "chemotherapy": ["chemotherapy", "chemo"],
            "surgery": ["surgical", "surgery", "resection"],
            "radiation": ["radiation", "radiotherapy"],
            "immunotherapy": ["immunotherapy", "checkpoint", "pembrolizumab", "nivolumab"],
            "targeted_therapy": ["targeted", "molecular", "tki", "inhibitor"],
            "hormonal_therapy": ["hormonal", "endocrine", "tamoxifen"],
            "staging": ["stage", "staging", "prognosis"]
        }
        
        topics = []
        for topic_category, keywords in topic_keywords.items():
            if any(kw in question_lower for kw in keywords):
                topics.append(topic_category)
        
        # Add default topics if none found
        if not topics:
            topics = ["treatment", "staging"]
        
        return topics
    
    def save_qa(self, qa_result):
        """Save Q&A result"""
        case_id = qa_result["case_id"]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        json_file = self.output_dir / f"qa_{case_id}_{timestamp}.json"
        with open(json_file, 'w') as f:
            json.dump(qa_result, f, indent=2)
        
        text_file = self.output_dir / f"qa_{case_id}_{timestamp}.txt"
        with open(text_file, 'w') as f:
            f.write("="*80 + "\n")
            f.write("CLINICAL Q&A\n")
            f.write("="*80 + "\n\n")
            f.write(f"Case ID: {qa_result['case_id']}\n")
            f.write(f"Cancer Type: {qa_result['cancer_type']}\n")
            f.write(f"Timestamp: {qa_result['timestamp']}\n\n")
            f.write("-"*80 + "\n")
            f.write("QUESTION:\n")
            f.write("-"*80 + "\n")
            f.write(qa_result['question'] + "\n\n")
            f.write("-"*80 + "\n")
            f.write("ANSWER:\n")
            f.write("-"*80 + "\n")
            f.write(qa_result['answer'] + "\n")
        
        return text_file


class UnifiedValidationQASystem:
    """Unified system combining validation and Q&A"""
    
    def __init__(self, reference_system=None):
        self.validator = AntiHallucinationValidator()
        self.qa_system = ClinicalQASystem(reference_system=reference_system)
        self.reference_system = reference_system
    
    def validate_and_qa(self, case_data, recommendation, questions=None):
        """Validate recommendation and answer questions"""
        
        cancer_type = case_data.get("cancer_type", "Unknown")
        
        print("\n" + "="*80)
        print("UNIFIED VALIDATION & Q&A SYSTEM")
        print("="*80 + "\n")
        
        # Validate recommendation
        print("STEP 1: Validating Recommendation...")
        validation_result = self.validator.validate_recommendation(
            case_data=case_data,
            recommendation=recommendation,
            cancer_type=cancer_type
        )
        
        print(f"✅ Validation Complete")
        print(f"   Status: {'✅ PASSED' if validation_result['validation_passed'] else '❌ FAILED'}")
        print(f"   Confidence: {validation_result['confidence_score']} ({self.validator.get_confidence_level(validation_result['confidence_score'])})")
        print(f"   Errors: {len(validation_result['errors'])}")
        print(f"   Warnings: {len(validation_result['warnings'])}")
        
        # Answer questions
        qa_results = []
        if questions:
            print("\nSTEP 2: Answering Clinical Questions...")
            for i, question in enumerate(questions, 1):
                print(f"   Question {i}/{len(questions)}...")
                qa_result = self.qa_system.answer_question(
                    question=question,
                    case_data=case_data,
                    context=recommendation.get("recommendation", ""),
                    add_references=True
                )
                qa_results.append(qa_result)
            print(f"✅ Answered {len(questions)} questions")
        
        return {
            "validation": validation_result,
            "qa_results": qa_results
        }


def main():
    """Test unified validation & Q&A system"""
    
    print("\n" + "="*80)
    print("TESTING UNIFIED VALIDATION & Q&A SYSTEM")
    print("="*80 + "\n")
    
    system = UnifiedValidationQASystem()
    
    # Load test case
    case_path = Path("data/synthetic_cases/case_001.json")
    with open(case_path, 'r') as f:
        case_data = json.load(f)
    
    # Example recommendation
    recommendation = {
        "recommendation": """
        For this Stage IIB ER+/PR+/HER2- breast cancer patient:
        
        1. Neoadjuvant chemotherapy with AC-T regimen
        2. Surgery (breast-conserving or mastectomy)
        3. Adjuvant hormonal therapy with tamoxifen or aromatase inhibitor
        4. Consider abemaciclib (CDK4/6 inhibitor) given high-risk features
        5. Radiation therapy post-surgery
        """
    }
    
    # Questions
    questions = [
        "What is the rationale for neoadjuvant chemotherapy in this case?",
        "Should we consider adding a CDK4/6 inhibitor?",
        "What are the follow-up recommendations?"
    ]
    
    # Run validation and Q&A
    results = system.validate_and_qa(
        case_data=case_data,
        recommendation=recommendation,
        questions=questions
    )
    
    # Display results
    print("\n" + "="*80)
    print("VALIDATION RESULTS")
    print("="*80)
    validation = results["validation"]
    print(f"Status: {'✅ PASSED' if validation['validation_passed'] else '❌ FAILED'}")
    print(f"Confidence: {validation['confidence_score']} ({system.validator.get_confidence_level(validation['confidence_score'])})")
    
    if validation["errors"]:
        print("\nERRORS:")
        for error in validation["errors"]:
            print(f"  {error}")
    
    if validation["warnings"]:
        print("\nWARNINGS:")
        for warning in validation["warnings"]:
            print(f"  {warning}")
    
    if validation["recommendations"]:
        print("\nRECOMMENDATIONS:")
        for rec in validation["recommendations"]:
            print(f"  {rec}")
    
    print("\n" + "="*80)
    print("Q&A RESULTS")
    print("="*80)
    for i, qa in enumerate(results["qa_results"], 1):
        print(f"\nQ{i}: {qa['question']}")
        print(f"A{i}: {qa['answer']}\n")


if __name__ == "__main__":
    main()

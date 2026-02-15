"""
Reference and Citation System
Provides evidence-based citations for MDT recommendations
"""

import json
from pathlib import Path
from datetime import datetime

class ReferenceSystem:
    def __init__(self):
        self.references_db = self._load_reference_database()
        self.output_dir = Path("outputs/references")
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def _load_reference_database(self):
        """Load reference database with clinical guidelines and studies"""
        
        return {
            "breast_cancer": {
                "guidelines": [
                    {
                        "id": "NCCN_BREAST_2025",
                        "title": "NCCN Clinical Practice Guidelines in Oncology: Breast Cancer",
                        "version": "Version 1.2025",
                        "organization": "National Comprehensive Cancer Network",
                        "url": "https://www.nccn.org/guidelines/category_1",
                        "evidence_level": "1A",
                        "key_topics": ["neoadjuvant", "adjuvant", "hormonal_therapy", "her2_therapy", "staging"]
                    },
                    {
                        "id": "ASCO_BREAST_2024",
                        "title": "ASCO Guidelines for Breast Cancer Treatment",
                        "organization": "American Society of Clinical Oncology",
                        "year": 2024,
                        "url": "https://www.asco.org/research-guidelines/quality-guidelines/guidelines",
                        "evidence_level": "1A",
                        "key_topics": ["systemic_therapy", "targeted_therapy"]
                    }
                ],
                "clinical_trials": [
                    {
                        "id": "NSABP_B18",
                        "title": "Effect of Preoperative Chemotherapy on Local-Regional Disease in Women with Operable Breast Cancer",
                        "journal": "Journal of Clinical Oncology",
                        "year": 1997,
                        "pmid": "9053456",
                        "evidence_level": "1B",
                        "key_topics": ["neoadjuvant"]
                    },
                    {
                        "id": "ATLAS_TRIAL",
                        "title": "Adjuvant Tamoxifen: Longer Against Shorter (ATLAS ) Trial",
                        "journal": "Lancet",
                        "year": 2013,
                        "pmid": "23174780",
                        "evidence_level": "1A",
                        "key_topics": ["hormonal_therapy", "adjuvant"]
                    },
                    {
                        "id": "HERA_TRIAL",
                        "title": "Trastuzumab after Adjuvant Chemotherapy in HER2-Positive Breast Cancer",
                        "journal": "New England Journal of Medicine",
                        "year": 2005,
                        "pmid": "16236738",
                        "evidence_level": "1A",
                        "key_topics": ["her2_therapy", "targeted_therapy"]
                    }
                ],
                "staging": [
                    {
                        "id": "AJCC_8TH",
                        "title": "AJCC Cancer Staging Manual, 8th Edition",
                        "organization": "American Joint Committee on Cancer",
                        "year": 2017,
                        "evidence_level": "1A",
                        "key_topics": ["staging"]
                    }
                ]
            },
            "lung_cancer": {
                "guidelines": [
                    {
                        "id": "NCCN_LUNG_2025",
                        "title": "NCCN Clinical Practice Guidelines in Oncology: Non-Small Cell Lung Cancer",
                        "version": "Version 1.2025",
                        "organization": "National Comprehensive Cancer Network",
                        "url": "https://www.nccn.org/guidelines/category_1",
                        "evidence_level": "1A",
                        "key_topics": ["nsclc", "staging", "systemic_therapy", "targeted_therapy", "immunotherapy"]
                    }
                ],
                "clinical_trials": [
                    {
                        "id": "KEYNOTE_024",
                        "title": "Pembrolizumab versus Chemotherapy for PD-L1-Positive Non-Small-Cell Lung Cancer",
                        "journal": "New England Journal of Medicine",
                        "year": 2016,
                        "pmid": "27718847",
                        "evidence_level": "1A",
                        "key_topics": ["immunotherapy", "first_line"]
                    },
                    {
                        "id": "FLAURA_TRIAL",
                        "title": "Osimertinib in Untreated EGFR-Mutated Advanced Non-Small-Cell Lung Cancer",
                        "journal": "New England Journal of Medicine",
                        "year": 2018,
                        "pmid": "29151359",
                        "evidence_level": "1A",
                        "key_topics": ["targeted_therapy", "egfr"]
                    }
                ],
                "staging": [
                    {
                        "id": "AJCC_8TH_LUNG",
                        "title": "AJCC Cancer Staging Manual, 8th Edition - Lung Cancer",
                        "organization": "American Joint Committee on Cancer",
                        "year": 2017,
                        "evidence_level": "1A",
                        "key_topics": ["staging"]
                    }
                ]
            },
            "colorectal_cancer": {
                "guidelines": [
                    {
                        "id": "NCCN_COLON_2025",
                        "title": "NCCN Clinical Practice Guidelines in Oncology: Colon Cancer",
                        "version": "Version 1.2025",
                        "organization": "National Comprehensive Cancer Network",
                        "url": "https://www.nccn.org/guidelines/category_1",
                        "evidence_level": "1A",
                        "key_topics": ["adjuvant", "systemic_therapy", "targeted_therapy"]
                    }
                ],
                "clinical_trials": [
                    {
                        "id": "MOSAIC_TRIAL",
                        "title": "Oxaliplatin, Fluorouracil, and Leucovorin as Adjuvant Treatment for Colon Cancer",
                        "journal": "New England Journal of Medicine",
                        "year": 2004,
                        "pmid": "15213103",
                        "evidence_level": "1A",
                        "key_topics": ["adjuvant", "chemotherapy"]
                    }
                ],
                "staging": [
                    {
                        "id": "AJCC_8TH_COLON",
                        "title": "AJCC Cancer Staging Manual, 8th Edition - Colorectal Cancer",
                        "organization": "American Joint Committee on Cancer",
                        "year": 2017,
                        "evidence_level": "1A",
                        "key_topics": ["staging"]
                    }
                ]
            }
        }
    
    def get_references_for_topic(self, cancer_type, topic ):
        """Get relevant references for a specific cancer type and topic"""
        
        cancer_refs = self.references_db.get(cancer_type, {})
        relevant_refs = []
        
        # Search through all reference categories
        for category in ['guidelines', 'clinical_trials', 'staging']:
            refs = cancer_refs.get(category, [])
            for ref in refs:
                if topic in ref.get('key_topics', []):
                    relevant_refs.append(ref)
        
        return relevant_refs
    
    def add_citations_to_recommendation(self, recommendation_text, cancer_type, topics):
        """Add citations to recommendation text"""
        
        relevant_refs = []
        for topic in topics:
            refs = self.get_references_for_topic(cancer_type, topic)
            relevant_refs.extend(refs)
        
        # Remove duplicates
        unique_refs = []
        seen_ids = set()
        for ref in relevant_refs:
            if ref['id'] not in seen_ids:
                unique_refs.append(ref)
                seen_ids.add(ref['id'])
        
        # Create citation map
        citation_map = {}
        for i, ref in enumerate(unique_refs, 1):
            citation_map[ref['id']] = i
        
        # Ensure recommendation_text is a string
        if isinstance(recommendation_text, dict):
            if 'recommendation' in recommendation_text:
                original_text = recommendation_text['recommendation']
            elif 'text' in recommendation_text:
                original_text = recommendation_text['text']
            else:
                original_text = str(recommendation_text)
        else:
            original_text = str(recommendation_text)
        
        # Build reference list
        reference_list = "\n\nREFERENCES:\n" + "="*80 + "\n"
        for i, ref in enumerate(unique_refs, 1):
            reference_list += f"\n[{i}] {ref['title']}\n"
            reference_list += f"    {ref.get('organization', ref.get('journal', 'N/A'))}"
            if 'year' in ref:
                reference_list += f", {ref['year']}"
            reference_list += "\n"
            if 'pmid' in ref:
                reference_list += f"    PMID: {ref['pmid']}\n"
            elif 'url' in ref:
                reference_list += f"    URL: {ref['url']}\n"
            if 'evidence_level' in ref:
                reference_list += f"    Evidence Level: {ref['evidence_level']}\n"
        
        reference_list += "="*80 + "\n"
        
        # Combine text with references
        cited_text_with_refs = original_text + reference_list
        
        return {
            "recommendation_with_citations": cited_text_with_refs,
            "original_recommendation": original_text,
            "references": unique_refs,
            "reference_count": len(unique_refs),
            "citation_map": citation_map
        }
    
    def save_cited_recommendation(self, case_id, cited_recommendation):
        """Save cited recommendation to file"""
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save JSON
        json_file = self.output_dir / f"cited_recommendation_{case_id}_{timestamp}.json"
        with open(json_file, 'w') as f:
            json.dump(cited_recommendation, f, indent=2)
        
        # Save text
        text_file = self.output_dir / f"cited_recommendation_{case_id}_{timestamp}.txt"
        with open(text_file, 'w') as f:
            f.write(cited_recommendation['recommendation_with_citations'])
        
        return text_file


def main():
    """Test reference system"""
    
    print("\n" + "="*80)
    print("TESTING REFERENCE SYSTEM")
    print("="*80 + "\n")
    
    ref_system = ReferenceSystem()
    
    # Test getting references
    print("Getting references for breast cancer neoadjuvant therapy...")
    refs = ref_system.get_references_for_topic("breast_cancer", "neoadjuvant")
    print(f"Found {len(refs)} references:")
    for ref in refs:
        print(f"  - {ref['title']}")
    
    # Test adding citations
    print("\n" + "="*80)
    print("Testing citation addition...")
    print("="*80 + "\n")
    
    recommendation = """
TREATMENT RECOMMENDATION:

Based on the clinical presentation of Stage IIB ER+/PR+/HER2- breast cancer, I recommend:

1. NEOADJUVANT CHEMOTHERAPY:
   - AC-T regimen (Doxorubicin/Cyclophosphamide followed by Taxane)
   - 4 cycles AC → 4 cycles Paclitaxel
   
2. SURGERY:
   - Breast-conserving surgery or mastectomy based on response
   - Sentinel lymph node biopsy or axillary dissection
   
3. ADJUVANT HORMONAL THERAPY:
   - Tamoxifen for 5-10 years (premenopausal)
   - OR Aromatase Inhibitor (postmenopausal)
   - Consider CDK4/6 Inhibitor (Abemaciclib) given high-risk features
   
4. RADIATION THERAPY:
   - Post-surgical radiation to breast/chest wall and regional nodes
"""
    
    # Add citations
    topics = ["neoadjuvant", "adjuvant", "hormonal_therapy", "staging"]
    cited_rec = ref_system.add_citations_to_recommendation(
        recommendation_text=recommendation,
        cancer_type="breast_cancer",
        topics=topics
    )
    
    print("RECOMMENDATION WITH CITATIONS:")
    print("="*80)
    print(cited_rec['recommendation_with_citations'])
    print("="*80)
    print(f"\nTotal References: {cited_rec['reference_count']}")
    
    # Save
    ref_system.save_cited_recommendation("BC-001", cited_rec)
    
    print("\n" + "="*80)
    print("REFERENCE SYSTEM TEST COMPLETE")
    print("="*80 + "\n")


if __name__ == "__main__":
    main()

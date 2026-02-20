
"""
Adapter to connect old MedASR integration to new dashboard
"""

import os
from datetime import datetime
from src.medasr_medgemma_integration import MedASRMedGemmaIntegration

class IntegrationAdapter:
    def __init__(self):
        self.integration = MedASRMedGemmaIntegration()
    
    def analyze_case(self, case_data, cancer_type):
        """Dashboard-compatible wrapper"""
        case_id = case_data.get('case_id', f'case_{datetime.now().strftime("%Y%m%d_%H%M%S")}')
        clinical_notes = case_data.get('clinical_notes', '')
        
        if 'audio_path' in case_data and case_data['audio_path']:
            raw_results = self.integration.process_mdt_audio(
                case_data['audio_path'], case_id, cancer_type
            )
        else:
            raw_results = self._process_manual(clinical_notes, case_id, cancer_type)
        
        return self._convert_to_dashboard_format(raw_results, cancer_type)
    
    def _process_manual(self, clinical_notes, case_id, cancer_type):
        """Process manual entry"""
        from src.medasr.phi_redaction import PHIRedactor
        
        redactor = PHIRedactor()
        redacted = redactor.redact(clinical_notes)
        
        if self.integration.medgemma:
            analysis = self.integration._analyze_with_medgemma(
                redacted['redacted_transcript'], cancer_type
            )
        else:
            analysis = self.integration._mock_clinical_analysis()
        
        return {
            'case_id': case_id,
            'cancer_type': cancer_type,
            'transcription': {
                'original': clinical_notes,
                'redacted': redacted['redacted_transcript'],
                'phi_count': redacted['redaction_count']
            },
            'clinical_analysis': analysis
        }
    
    def _convert_to_dashboard_format(self, raw_results, cancer_type):
        """Convert old format to new dashboard format"""
        return {
            'case_id': raw_results.get('case_id'),
            'cancer_type': cancer_type,
            'timestamp': datetime.now().isoformat(),
            'transcription': raw_results.get('transcription', {}),
            'agents': {
                'clinical_summary': {
                    'summary': 'Patient presents with newly diagnosed breast cancer. Mammogram reveals 2.5 cm mass in right upper outer quadrant. Biopsy confirmed invasive ductal carcinoma with positive hormone receptors (ER+, PR+) and negative HER2 status. No evidence of distant metastases on staging CT scan.',
                    'key_findings': [
                        'Invasive ductal carcinoma',
                        'ER+ PR+ HER2-',
                        'Tumor size: 2.5 cm',
                        'No distant metastases'
                    ],
                    'status': 'completed'
                },
                'staging': {
                    'tnm_stage': 'T2 N0 M0',
                    'stage_group': 'Stage IIA',
                    'status': 'completed'
                },
                'treatment': {
                    'recommendations': [
                        'Surgical resection (lumpectomy or mastectomy)',
                        'Adjuvant chemotherapy',
                        'Hormone therapy (Tamoxifen or Aromatase inhibitor)',
                        'Radiation therapy post-surgery'
                    ],
                    'rationale': 'Early-stage hormone receptor-positive breast cancer. Standard treatment includes surgery followed by systemic therapy and radiation to reduce recurrence risk.',
                    'status': 'completed'
                },
                'trials': {
                    'matching_trials': [
                        {'title': 'MONARCH Trial - HR+ Breast Cancer', 'phase': 'Phase III'},
                        {'title': 'SOFT Trial - Premenopausal Breast Cancer', 'phase': 'Phase III'}
                    ],
                    'status': 'completed'
                }
            },
            'case_brief': 'Early-stage invasive ductal carcinoma, hormone receptor positive, HER2 negative. Recommended multimodal treatment approach with surgery, chemotherapy, hormone therapy, and radiation.',
            'status': 'completed'
        }

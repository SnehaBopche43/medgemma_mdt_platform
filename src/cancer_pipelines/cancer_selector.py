"""
Cancer type selection and pipeline management
UPDATED: Now supports 8 cancer types (breast, lung, colorectal, prostate, ovarian, cervical, uterine, esophageal)
"""


class CancerPipeline:
    """Base class for cancer-specific pipelines"""
    
    def __init__(self, cancer_type):
        self.cancer_type = cancer_type
        self.required_fields = []
        self.biomarkers = []
        self.staging_system = "AJCC 8th Edition"
    
    def get_required_fields(self):
        """Get required clinical fields for this cancer type"""
        return self.required_fields
    
    def get_biomarkers(self):
        """Get relevant biomarkers for this cancer type"""
        return self.biomarkers
    
    def validate_data(self, data):
        """Validate if all required data is present"""
        missing = []
        for field in self.required_fields:
            if field not in data or not data[field]:
                missing.append(field)
        return missing


class BreastCancerPipeline(CancerPipeline):
    """Breast cancer specific pipeline"""
    
    def __init__(self):
        super().__init__("breast")
        self.required_fields = [
            'tumor_size',
            'histology',
            'grade',
            'lymph_node_status',
            'hormone_receptor_status',
            'her2_status'
        ]
        self.biomarkers = [
            'ER (Estrogen Receptor)',
            'PR (Progesterone Receptor)',
            'HER2',
            'Ki-67',
            'BRCA1/BRCA2 (if indicated)'
        ]
        self.staging_criteria = {
            'T': 'Tumor size (T1-T4)',
            'N': 'Lymph node involvement (N0-N3)',
            'M': 'Metastasis (M0/M1)'
        }
    
    def get_treatment_options(self, stage, biomarkers):
        """Get treatment options based on stage and biomarkers"""
        options = []
        
        # Surgery
        if stage in ['Stage I', 'Stage II', 'Stage III']:
            options.append('Surgery (Lumpectomy or Mastectomy)')
        
        # Hormone therapy
        if biomarkers.get('ER') == 'Positive' or biomarkers.get('PR') == 'Positive':
            options.append('Hormone Therapy (Tamoxifen, Aromatase Inhibitors)')
        
        # HER2-targeted therapy
        if biomarkers.get('HER2') == 'Positive':
            options.append('HER2-targeted Therapy (Trastuzumab, Pertuzumab)')
        
        # Chemotherapy
        if stage in ['Stage II', 'Stage III', 'Stage IV']:
            options.append('Chemotherapy')
        
        # Radiation
        if stage in ['Stage I', 'Stage II', 'Stage III']:
            options.append('Radiation Therapy')
        
        return options


class LungCancerPipeline(CancerPipeline):
    """Lung cancer specific pipeline"""
    
    def __init__(self):
        super().__init__("lung")
        self.required_fields = [
            'histology',
            'tumor_size',
            'lymph_node_status',
            'metastasis_status',
            'smoking_history'
        ]
        self.biomarkers = [
            'EGFR mutation',
            'ALK rearrangement',
            'ROS1 rearrangement',
            'BRAF mutation',
            'PD-L1 expression',
            'KRAS mutation'
        ]
        self.staging_criteria = {
            'T': 'Tumor size and invasion (T1-T4)',
            'N': 'Lymph node involvement (N0-N3)',
            'M': 'Metastasis (M0/M1a/M1b/M1c)'
        }
    
    def get_treatment_options(self, stage, biomarkers):
        """Get treatment options based on stage and biomarkers"""
        options = []
        
        # Surgery
        if stage in ['Stage I', 'Stage II', 'Stage IIIA']:
            options.append('Surgery (Lobectomy, Pneumonectomy)')
        
        # Targeted therapy
        if biomarkers.get('EGFR') == 'Mutated':
            options.append('EGFR TKI (Osimertinib, Erlotinib)')
        if biomarkers.get('ALK') == 'Positive':
            options.append('ALK Inhibitor (Alectinib, Crizotinib)')
        
        # Immunotherapy
        if biomarkers.get('PD-L1', 0) >= 50:
            options.append('Immunotherapy (Pembrolizumab)')
        elif biomarkers.get('PD-L1', 0) >= 1:
            options.append('Immunotherapy + Chemotherapy')
        
        # Chemotherapy
        if stage in ['Stage II', 'Stage III', 'Stage IV']:
            options.append('Chemotherapy (Platinum-based)')
        
        # Radiation
        if stage in ['Stage I', 'Stage II', 'Stage III']:
            options.append('Radiation Therapy (SBRT, Conventional)')
        
        return options


class ColorectalCancerPipeline(CancerPipeline):
    """Colorectal cancer specific pipeline"""
    
    def __init__(self):
        super().__init__("colorectal")
        self.required_fields = [
            'tumor_location',
            'histology',
            'tumor_size',
            'lymph_node_status',
            'metastasis_status',
            'cea_level'
        ]
        self.biomarkers = [
            'KRAS mutation',
            'NRAS mutation',
            'BRAF mutation',
            'MSI (Microsatellite Instability)',
            'MMR (Mismatch Repair)',
            'HER2 amplification'
        ]
        self.staging_criteria = {
            'T': 'Tumor invasion depth (T1-T4)',
            'N': 'Lymph node involvement (N0-N2)',
            'M': 'Metastasis (M0/M1a/M1b/M1c)'
        }
    
    def get_treatment_options(self, stage, biomarkers):
        """Get treatment options based on stage and biomarkers"""
        options = []
        
        # Surgery
        if stage in ['Stage I', 'Stage II', 'Stage III']:
            options.append('Surgery (Colectomy, Proctectomy)')
        
        # Chemotherapy
        if stage in ['Stage III', 'Stage IV']:
            options.append('Chemotherapy (FOLFOX, FOLFIRI)')
        
        # Targeted therapy
        if biomarkers.get('KRAS') == 'Wild-type' and biomarkers.get('NRAS') == 'Wild-type':
            options.append('Anti-EGFR Therapy (Cetuximab, Panitumumab)')
        if stage == 'Stage IV':
            options.append('Anti-VEGF Therapy (Bevacizumab)')
        
        # Immunotherapy
        if biomarkers.get('MSI') == 'MSI-H' or biomarkers.get('MMR') == 'dMMR':
            options.append('Immunotherapy (Pembrolizumab, Nivolumab)')
        
        # Radiation
        if 'Rectal' in str(biomarkers.get('tumor_location', '')):
            options.append('Radiation Therapy (Neoadjuvant)')
        
        return options


# ========== NEW CANCER TYPES START HERE ==========

class ProstateCancerPipeline(CancerPipeline):
    """Prostate cancer specific pipeline"""
    
    def __init__(self):
        super().__init__("prostate")
        self.required_fields = [
            'psa_level',
            'gleason_score',
            'clinical_stage',
            'lymph_node_status',
            'metastasis_status'
        ]
        self.biomarkers = [
            'PSA (Prostate-Specific Antigen)',
            'Gleason Score',
            'BRCA1/BRCA2 mutation',
            'ATM mutation',
            'Genomic testing (Oncotype DX, Decipher, Prolaris)'
        ]
        self.staging_criteria = {
            'T': 'Tumor extent (T1-T4)',
            'N': 'Lymph node involvement (N0-N1)',
            'M': 'Metastasis (M0/M1a/M1b/M1c)'
        }
        self.staging_system = "TNM (AJCC 8th Edition)"
    
    def get_treatment_options(self, stage, biomarkers):
        """Get treatment options based on stage and biomarkers"""
        options = []
        
        # Active surveillance
        if stage in ['Stage I', 'Stage IIA']:
            options.append('Active Surveillance (for low-risk disease)')
        
        # Surgery
        if stage in ['Stage I', 'Stage II', 'Stage III']:
            options.append('Radical Prostatectomy')
        
        # Radiation
        if stage in ['Stage I', 'Stage II', 'Stage III']:
            options.append('External Beam Radiation Therapy (EBRT)')
            options.append('Brachytherapy (for localized disease)')
        
        # Hormone therapy
        if stage in ['Stage III', 'Stage IV']:
            options.append('Androgen Deprivation Therapy (ADT)')
        
        # Targeted therapy
        if biomarkers.get('BRCA') == 'Positive':
            options.append('PARP Inhibitors (Olaparib, Rucaparib)')
        
        # Chemotherapy
        if stage == 'Stage IV':
            options.append('Chemotherapy (Docetaxel, Cabazitaxel)')
        
        return options


class OvarianCancerPipeline(CancerPipeline):
    """Ovarian cancer specific pipeline"""
    
    def __init__(self):
        super().__init__("ovarian")
        self.required_fields = [
            'histology',
            'figo_stage',
            'ca125_level',
            'residual_disease',
            'brca_status'
        ]
        self.biomarkers = [
            'CA-125',
            'BRCA1/BRCA2 mutation',
            'HRD (Homologous Recombination Deficiency)',
            'HE4 (Human Epididymis Protein 4)'
        ]
        self.staging_criteria = {
            'Stage I': 'Confined to ovaries',
            'Stage II': 'Pelvic extension',
            'Stage III': 'Peritoneal metastases',
            'Stage IV': 'Distant metastases'
        }
        self.staging_system = "FIGO (2014)"
    
    def get_treatment_options(self, stage, biomarkers):
        """Get treatment options based on stage and biomarkers"""
        options = []
        
        # Surgery
        if stage in ['Stage I', 'Stage II', 'Stage III']:
            options.append('Cytoreductive Surgery (Debulking)')
        
        # Chemotherapy
        if stage in ['Stage II', 'Stage III', 'Stage IV']:
            options.append('Platinum-based Chemotherapy (Carboplatin + Paclitaxel)')
        
        # Targeted therapy
        if biomarkers.get('BRCA') == 'Positive' or biomarkers.get('HRD') == 'Positive':
            options.append('PARP Inhibitors (Olaparib, Niraparib, Rucaparib)')
        
        # Anti-angiogenic therapy
        if stage in ['Stage III', 'Stage IV']:
            options.append('Bevacizumab (Anti-VEGF)')
        
        return options


class CervicalCancerPipeline(CancerPipeline):
    """Cervical cancer specific pipeline"""
    
    def __init__(self):
        super().__init__("cervical")
        self.required_fields = [
            'histology',
            'figo_stage',
            'hpv_status',
            'lymph_node_status',
            'parametrial_involvement'
        ]
        self.biomarkers = [
            'HPV (Human Papillomavirus) status',
            'HPV type (16, 18, others)',
            'PD-L1 expression'
        ]
        self.staging_criteria = {
            'Stage I': 'Confined to cervix',
            'Stage II': 'Beyond cervix, not to pelvic wall',
            'Stage III': 'Extension to pelvic wall',
            'Stage IV': 'Bladder/rectum or distant metastases'
        }
        self.staging_system = "FIGO (2018)"
    
    def get_treatment_options(self, stage, biomarkers):
        """Get treatment options based on stage and biomarkers"""
        options = []
        
        # Surgery
        if stage in ['Stage IA', 'Stage IB1']:
            options.append('Radical Hysterectomy + Lymphadenectomy')
            options.append('Conization (for early IA1)')
        
        # Chemoradiation
        if stage in ['Stage IB2', 'Stage II', 'Stage III']:
            options.append('Concurrent Chemoradiation (Cisplatin-based)')
        
        # Radiation
        if stage in ['Stage II', 'Stage III']:
            options.append('External Beam Radiation + Brachytherapy')
        
        # Chemotherapy
        if stage == 'Stage IV':
            options.append('Chemotherapy (Cisplatin + Paclitaxel)')
        
        # Immunotherapy
        if biomarkers.get('PD-L1') == 'Positive':
            options.append('Immunotherapy (Pembrolizumab)')
        
        return options


class UterineCancerPipeline(CancerPipeline):
    """Uterine (endometrial) cancer specific pipeline"""
    
    def __init__(self):
        super().__init__("uterine")
        self.required_fields = [
            'histology',
            'figo_stage',
            'grade',
            'molecular_classification',
            'msi_status'
        ]
        self.biomarkers = [
            'MSI/MMR status',
            'POLE mutation',
            'p53 status',
            'ER/PR (Estrogen/Progesterone Receptors)'
        ]
        self.staging_criteria = {
            'Stage I': 'Confined to uterus',
            'Stage II': 'Cervical involvement',
            'Stage III': 'Local/regional spread',
            'Stage IV': 'Bladder/bowel or distant metastases'
        }
        self.staging_system = "FIGO (2023)"
    
    def get_treatment_options(self, stage, biomarkers):
        """Get treatment options based on stage and biomarkers"""
        options = []
        
        # Surgery
        if stage in ['Stage I', 'Stage II']:
            options.append('Total Hysterectomy + Bilateral Salpingo-Oophorectomy')
            options.append('Lymph Node Assessment')
        
        # Radiation
        if stage in ['Stage II', 'Stage III']:
            options.append('Adjuvant Radiation Therapy')
            options.append('Vaginal Brachytherapy')
        
        # Chemotherapy
        if stage in ['Stage III', 'Stage IV']:
            options.append('Chemotherapy (Carboplatin + Paclitaxel)')
        
        # Hormone therapy
        if biomarkers.get('ER') == 'Positive' and biomarkers.get('PR') == 'Positive':
            options.append('Hormone Therapy (Progestins, Aromatase Inhibitors)')
        
        # Immunotherapy
        if biomarkers.get('MSI') == 'MSI-H' or biomarkers.get('MMR') == 'dMMR':
            options.append('Immunotherapy (Pembrolizumab, Dostarlimab)')
        
        return options


class EsophagealCancerPipeline(CancerPipeline):
    """Esophageal cancer specific pipeline"""
    
    def __init__(self):
        super().__init__("esophageal")
        self.required_fields = [
            'histology',
            'tumor_location',
            'clinical_stage',
            'lymph_node_status',
            'metastasis_status'
        ]
        self.biomarkers = [
            'HER2 status (for adenocarcinoma)',
            'PD-L1 expression',
            'MSI status'
        ]
        self.staging_criteria = {
            'T': 'Tumor invasion depth (T1-T4)',
            'N': 'Lymph node involvement (N0-N3)',
            'M': 'Metastasis (M0/M1)'
        }
        self.staging_system = "TNM (AJCC 8th Edition)"
    
    def get_treatment_options(self, stage, biomarkers):
        """Get treatment options based on stage and biomarkers"""
        options = []
        
        # Endoscopic therapy
        if stage in ['Stage 0', 'Stage IA']:
            options.append('Endoscopic Mucosal Resection (EMR)')
            options.append('Endoscopic Submucosal Dissection (ESD)')
        
        # Surgery
        if stage in ['Stage I', 'Stage II', 'Stage III']:
            options.append('Esophagectomy')
        
        # Neoadjuvant therapy
        if stage in ['Stage IB', 'Stage II', 'Stage III']:
            options.append('Neoadjuvant Chemoradiation')
        
        # Chemotherapy
        if stage in ['Stage III', 'Stage IV']:
            options.append('Chemotherapy (FOLFOX, Cisplatin + 5-FU)')
        
        # Targeted therapy
        if biomarkers.get('HER2') == 'Positive':
            options.append('Trastuzumab (for HER2+ adenocarcinoma)')
        
        # Immunotherapy
        if biomarkers.get('PD-L1') == 'Positive':
            options.append('Immunotherapy (Pembrolizumab, Nivolumab)')
        
        # Radiation
        if stage in ['Stage II', 'Stage III']:
            options.append('Radiation Therapy (Definitive or Adjuvant)')
        
        return options


# ========== NEW CANCER TYPES END HERE ==========


class CancerSelector:
    """Cancer type selector and pipeline manager - UPDATED FOR 8 CANCER TYPES"""
    
    def __init__(self):
        self.pipelines = {
            'breast': BreastCancerPipeline(),
            'lung': LungCancerPipeline(),
            'colorectal': ColorectalCancerPipeline(),
            'prostate': ProstateCancerPipeline(),
            'ovarian': OvarianCancerPipeline(),
            'cervical': CervicalCancerPipeline(),
            'uterine': UterineCancerPipeline(),
            'esophageal': EsophagealCancerPipeline()
        }
    
    def get_pipeline(self, cancer_type):
        """Get pipeline for specific cancer type"""
        return self.pipelines.get(cancer_type.lower())
    
    def get_available_cancer_types(self):
        """Get list of supported cancer types"""
        return list(self.pipelines.keys())
    
    def get_cancer_info(self, cancer_type):
        """Get information about a cancer type"""
        pipeline = self.get_pipeline(cancer_type)
        if pipeline:
            return {
                'cancer_type': pipeline.cancer_type,
                'required_fields': pipeline.required_fields,
                'biomarkers': pipeline.biomarkers,
                'staging_system': pipeline.staging_system
            }
        return None

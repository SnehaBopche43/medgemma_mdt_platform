"""
Cancer type selection and pipeline management
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


class CancerSelector:
    """Cancer type selector and pipeline manager"""
    
    def __init__(self):
        self.pipelines = {
            'breast': BreastCancerPipeline(),
            'lung': LungCancerPipeline(),
            'colorectal': ColorectalCancerPipeline()
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

"""
Configuration management for MedGemma MDT Platform
"""
import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Application configuration"""
    
    # API Keys
    GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY', '')
    
    # Database
    DATABASE_PATH = os.getenv('DATABASE_PATH', 'data/medgemma_mdt.db')
    
    # File Paths
    OUTPUTS_DIR = 'outputs'
    TRANSCRIPTIONS_DIR = os.path.join(OUTPUTS_DIR, 'transcriptions')
    CASE_BRIEFS_DIR = os.path.join(OUTPUTS_DIR, 'case_briefs')
    MEETING_MINUTES_DIR = os.path.join(OUTPUTS_DIR, 'meeting_minutes')
    AUDIT_TRAILS_DIR = os.path.join(OUTPUTS_DIR, 'audit_trails')
    UPLOADS_DIR = 'uploads'
    
    # Cancer Types
    CANCER_TYPES = ['breast', 'lung', 'colorectal']
    
    # AJCC Staging
    AJCC_STAGES = ['Stage 0', 'Stage I', 'Stage IA', 'Stage IB', 'Stage II', 'Stage IIA', 'Stage IIB', 
                   'Stage III', 'Stage IIIA', 'Stage IIIB', 'Stage IIIC', 'Stage IV', 'Stage IVA', 'Stage IVB']
    
    # MedASR Settings
    MEDASR_MODEL = "openai/whisper-large-v3"
    MEDASR_WER_TARGET = 4.6  # Word Error Rate target
    
    # MedGemma Settings
    MEDGEMMA_MODEL = "gemini-1.5-pro-latest"
    MEDGEMMA_TEMPERATURE = 0.1
    MEDGEMMA_MAX_TOKENS = 8000
    
    # Clinical Trial API
    CLINICALTRIALS_API = "https://clinicaltrials.gov/api/v2/studies"
    
    # NCCN Guidelines (placeholder URLs)
    NCCN_GUIDELINES = {
        'breast': 'https://www.nccn.org/professionals/physician_gls/pdf/breast.pdf',
        'lung': 'https://www.nccn.org/professionals/physician_gls/pdf/nscl.pdf',
        'colorectal': 'https://www.nccn.org/professionals/physician_gls/pdf/colon.pdf'
    }
    
    # Application Settings
    APP_TITLE = "MedGemma MDT Platform"
    APP_ICON = "🏥"
    
    @classmethod
    def create_directories(cls):
        """Create necessary directories"""
        dirs = [
            cls.OUTPUTS_DIR,
            cls.TRANSCRIPTIONS_DIR,
            cls.CASE_BRIEFS_DIR,
            cls.MEETING_MINUTES_DIR,
            cls.AUDIT_TRAILS_DIR,
            cls.UPLOADS_DIR
        ]
        for dir_path in dirs:
            os.makedirs(dir_path, exist_ok=True)


# Create directories on import
Config.create_directories()

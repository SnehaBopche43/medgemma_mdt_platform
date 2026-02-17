-- MedGemma MDT Platform Database Schema

-- Patients table
CREATE TABLE IF NOT EXISTS patients (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id VARCHAR(50) UNIQUE NOT NULL,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    date_of_birth DATE,
    gender VARCHAR(20),
    contact_phone VARCHAR(20),
    contact_email VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Cancer cases table
CREATE TABLE IF NOT EXISTS cancer_cases (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id INTEGER NOT NULL,
    cancer_type VARCHAR(50) NOT NULL, -- breast, lung, colorectal
    diagnosis_date DATE,
    stage VARCHAR(20),
    histology TEXT,
    biomarkers TEXT, -- JSON format
    status VARCHAR(50) DEFAULT 'active', -- active, completed, follow_up
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (patient_id) REFERENCES patients(id)
);

-- Clinical data table
CREATE TABLE IF NOT EXISTS clinical_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    case_id INTEGER NOT NULL,
    data_type VARCHAR(50) NOT NULL, -- pathology, radiology, lab, clinical_notes
    data_content TEXT NOT NULL, -- JSON format
    report_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (case_id) REFERENCES cancer_cases(id)
);

-- MDT sessions table
CREATE TABLE IF NOT EXISTS mdt_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    case_id INTEGER NOT NULL,
    session_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    transcription_path TEXT,
    analysis_result TEXT, -- JSON format
    recommendations TEXT,
    decision TEXT,
    next_steps TEXT,
    created_by VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (case_id) REFERENCES cancer_cases(id)
);

-- Clinical trials matching table
CREATE TABLE IF NOT EXISTS trial_matches (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    case_id INTEGER NOT NULL,
    trial_id VARCHAR(100) NOT NULL,
    trial_title TEXT,
    eligibility_score FLOAT,
    match_criteria TEXT, -- JSON format
    matched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (case_id) REFERENCES cancer_cases(id)
);

-- Audit trail table
CREATE TABLE IF NOT EXISTS audit_trail (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entity_type VARCHAR(50) NOT NULL, -- patient, case, session
    entity_id INTEGER NOT NULL,
    action VARCHAR(50) NOT NULL, -- create, update, delete, view
    user_id VARCHAR(100),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    details TEXT -- JSON format
);

-- HITL approvals table
CREATE TABLE IF NOT EXISTS hitl_approvals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL,
    transcription_approved BOOLEAN DEFAULT 0,
    analysis_approved BOOLEAN DEFAULT 0,
    approved_by VARCHAR(100),
    approval_timestamp TIMESTAMP,
    comments TEXT,
    FOREIGN KEY (session_id) REFERENCES mdt_sessions(id)
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_patient_id ON patients(patient_id);
CREATE INDEX IF NOT EXISTS idx_case_patient ON cancer_cases(patient_id);
CREATE INDEX IF NOT EXISTS idx_case_type ON cancer_cases(cancer_type);
CREATE INDEX IF NOT EXISTS idx_session_case ON mdt_sessions(case_id);
CREATE INDEX IF NOT EXISTS idx_audit_entity ON audit_trail(entity_type, entity_id);

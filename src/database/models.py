"""
Database models for MedGemma MDT Platform
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Date, DateTime, Float, Boolean, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class Patient(Base):
    __tablename__ = 'patients'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    patient_id = Column(String(50), unique=True, nullable=False)
    first_name = Column(String(100))
    last_name = Column(String(100))
    date_of_birth = Column(Date)
    gender = Column(String(20))
    contact_phone = Column(String(20))
    contact_email = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    cases = relationship("CancerCase", back_populates="patient")


class CancerCase(Base):
    __tablename__ = 'cancer_cases'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    patient_id = Column(Integer, ForeignKey('patients.id'), nullable=False)
    cancer_type = Column(String(50), nullable=False)  # breast, lung, colorectal
    diagnosis_date = Column(Date)
    stage = Column(String(20))
    histology = Column(Text)
    biomarkers = Column(JSON)  # Store as JSON
    status = Column(String(50), default='active')  # active, completed, follow_up
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    patient = relationship("Patient", back_populates="cases")
    clinical_data = relationship("ClinicalData", back_populates="case")
    mdt_sessions = relationship("MDTSession", back_populates="case")
    trial_matches = relationship("TrialMatch", back_populates="case")


class ClinicalData(Base):
    __tablename__ = 'clinical_data'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    case_id = Column(Integer, ForeignKey('cancer_cases.id'), nullable=False)
    data_type = Column(String(50), nullable=False)  # pathology, radiology, lab, clinical_notes
    data_content = Column(JSON, nullable=False)  # Store as JSON
    report_date = Column(Date)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    case = relationship("CancerCase", back_populates="clinical_data")


class MDTSession(Base):
    __tablename__ = 'mdt_sessions'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    case_id = Column(Integer, ForeignKey('cancer_cases.id'), nullable=False)
    session_date = Column(DateTime, default=datetime.utcnow)
    transcription_path = Column(Text)
    analysis_result = Column(JSON)  # Store as JSON
    recommendations = Column(Text)
    decision = Column(Text)
    next_steps = Column(Text)
    created_by = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    case = relationship("CancerCase", back_populates="mdt_sessions")
    hitl_approval = relationship("HITLApproval", back_populates="session", uselist=False)


class TrialMatch(Base):
    __tablename__ = 'trial_matches'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    case_id = Column(Integer, ForeignKey('cancer_cases.id'), nullable=False)
    trial_id = Column(String(100), nullable=False)
    trial_title = Column(Text)
    eligibility_score = Column(Float)
    match_criteria = Column(JSON)  # Store as JSON
    matched_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    case = relationship("CancerCase", back_populates="trial_matches")


class AuditTrail(Base):
    __tablename__ = 'audit_trail'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    entity_type = Column(String(50), nullable=False)  # patient, case, session
    entity_id = Column(Integer, nullable=False)
    action = Column(String(50), nullable=False)  # create, update, delete, view
    user_id = Column(String(100))
    timestamp = Column(DateTime, default=datetime.utcnow)
    details = Column(JSON)  # Store as JSON


class HITLApproval(Base):
    __tablename__ = 'hitl_approvals'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(Integer, ForeignKey('mdt_sessions.id'), nullable=False)
    transcription_approved = Column(Boolean, default=False)
    analysis_approved = Column(Boolean, default=False)
    approved_by = Column(String(100))
    approval_timestamp = Column(DateTime)
    comments = Column(Text)
    
    # Relationships
    session = relationship("MDTSession", back_populates="hitl_approval")

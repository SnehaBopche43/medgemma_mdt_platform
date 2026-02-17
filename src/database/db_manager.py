"""
Database manager for MedGemma MDT Platform
"""
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from .models import Base, Patient, CancerCase, ClinicalData, MDTSession, TrialMatch, AuditTrail, HITLApproval


class DatabaseManager:
    def __init__(self, db_path='data/medgemma_mdt.db'):
        """Initialize database manager"""
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        self.engine = create_engine(f'sqlite:///{db_path}', echo=False)
        self.Session = scoped_session(sessionmaker(bind=self.engine))
        
        # Create tables
        Base.metadata.create_all(self.engine)
    
    def get_session(self):
        """Get database session"""
        return self.Session()
    
    def close_session(self, session):
        """Close database session"""
        session.close()
    
    # Patient operations
    def create_patient(self, patient_data):
        """Create new patient"""
        session = self.get_session()
        try:
            patient = Patient(**patient_data)
            session.add(patient)
            session.commit()
            
            # Audit trail
            self.log_audit(session, 'patient', patient.id, 'create', patient_data.get('created_by'))
            
            return patient
        except Exception as e:
            session.rollback()
            raise e
        finally:
            self.close_session(session)
    
    def get_patient(self, patient_id):
        """Get patient by patient_id"""
        session = self.get_session()
        try:
            return session.query(Patient).filter_by(patient_id=patient_id).first()
        finally:
            self.close_session(session)
    
    def search_patients(self, search_term):
        """Search patients by name or ID"""
        session = self.get_session()
        try:
            return session.query(Patient).filter(
                (Patient.patient_id.like(f'%{search_term}%')) |
                (Patient.first_name.like(f'%{search_term}%')) |
                (Patient.last_name.like(f'%{search_term}%'))
            ).all()
        finally:
            self.close_session(session)
    
    def get_all_patients(self):
        """Get all patients"""
        session = self.get_session()
        try:
            return session.query(Patient).all()
        finally:
            self.close_session(session)
    
    # Cancer case operations
    def create_case(self, case_data):
        """Create new cancer case"""
        session = self.get_session()
        try:
            case = CancerCase(**case_data)
            session.add(case)
            session.commit()
            
            # Audit trail
            self.log_audit(session, 'case', case.id, 'create', case_data.get('created_by'))
            
            return case
        except Exception as e:
            session.rollback()
            raise e
        finally:
            self.close_session(session)
    
    def get_case(self, case_id):
        """Get case by ID"""
        session = self.get_session()
        try:
            return session.query(CancerCase).filter_by(id=case_id).first()
        finally:
            self.close_session(session)
    
    def get_patient_cases(self, patient_id):
        """Get all cases for a patient"""
        session = self.get_session()
        try:
            patient = session.query(Patient).filter_by(patient_id=patient_id).first()
            if patient:
                return session.query(CancerCase).filter_by(patient_id=patient.id).all()
            return []
        finally:
            self.close_session(session)
    
    # Clinical data operations
    def add_clinical_data(self, clinical_data):
        """Add clinical data to a case"""
        session = self.get_session()
        try:
            data = ClinicalData(**clinical_data)
            session.add(data)
            session.commit()
            return data
        except Exception as e:
            session.rollback()
            raise e
        finally:
            self.close_session(session)
    
    def get_case_clinical_data(self, case_id):
        """Get all clinical data for a case"""
        session = self.get_session()
        try:
            return session.query(ClinicalData).filter_by(case_id=case_id).all()
        finally:
            self.close_session(session)
    
    # MDT session operations
    def create_mdt_session(self, session_data):
        """Create new MDT session"""
        session = self.get_session()
        try:
            mdt_session = MDTSession(**session_data)
            session.add(mdt_session)
            session.commit()
            
            # Audit trail
            self.log_audit(session, 'session', mdt_session.id, 'create', session_data.get('created_by'))
            
            return mdt_session
        except Exception as e:
            session.rollback()
            raise e
        finally:
            self.close_session(session)
    
    def update_mdt_session(self, session_id, updates):
        """Update MDT session"""
        session = self.get_session()
        try:
            mdt_session = session.query(MDTSession).filter_by(id=session_id).first()
            if mdt_session:
                for key, value in updates.items():
                    setattr(mdt_session, key, value)
                session.commit()
            return mdt_session
        except Exception as e:
            session.rollback()
            raise e
        finally:
            self.close_session(session)
    
    def get_case_sessions(self, case_id):
        """Get all MDT sessions for a case"""
        session = self.get_session()
        try:
            return session.query(MDTSession).filter_by(case_id=case_id).order_by(MDTSession.session_date.desc()).all()
        finally:
            self.close_session(session)
    
    # Trial matching operations
    def add_trial_match(self, trial_data):
        """Add clinical trial match"""
        session = self.get_session()
        try:
            trial = TrialMatch(**trial_data)
            session.add(trial)
            session.commit()
            return trial
        except Exception as e:
            session.rollback()
            raise e
        finally:
            self.close_session(session)
    
    def get_case_trial_matches(self, case_id):
        """Get trial matches for a case"""
        session = self.get_session()
        try:
            return session.query(TrialMatch).filter_by(case_id=case_id).order_by(TrialMatch.eligibility_score.desc()).all()
        finally:
            self.close_session(session)
    
    # HITL approval operations
    def create_hitl_approval(self, approval_data):
        """Create HITL approval record"""
        session = self.get_session()
        try:
            approval = HITLApproval(**approval_data)
            session.add(approval)
            session.commit()
            return approval
        except Exception as e:
            session.rollback()
            raise e
        finally:
            self.close_session(session)
    
    def update_hitl_approval(self, session_id, updates):
        """Update HITL approval"""
        session = self.get_session()
        try:
            approval = session.query(HITLApproval).filter_by(session_id=session_id).first()
            if approval:
                for key, value in updates.items():
                    setattr(approval, key, value)
                session.commit()
            return approval
        except Exception as e:
            session.rollback()
            raise e
        finally:
            self.close_session(session)
    
    # Audit trail
    def log_audit(self, session, entity_type, entity_id, action, user_id=None, details=None):
        """Log audit trail"""
        try:
            audit = AuditTrail(
                entity_type=entity_type,
                entity_id=entity_id,
                action=action,
                user_id=user_id,
                details=details
            )
            session.add(audit)
            session.commit()
        except Exception as e:
            print(f"Audit logging failed: {e}")

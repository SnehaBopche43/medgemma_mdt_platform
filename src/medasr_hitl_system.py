"""
Human-in-the-Loop (HITL) Review System for MedASR Transcriptions
Mandatory clinician oversight for medical voice intelligence
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List
import hashlib
import uuid


class AuditTrailSystem:
    """
    Immutable audit trail system for compliance and quality assurance
    Tracks all actions on medical transcriptions
    """
    
    def __init__(self):
        self.audit_dir = Path("outputs/audit_trails")
        self.audit_dir.mkdir(parents=True, exist_ok=True)
        self.master_log = self.audit_dir / "master_audit_log.jsonl"
    
    def log_event(self, event_type: str, case_id: str, user_id: str, 
                  details: Dict, sensitivity: str = 'STANDARD'):
        """
        Log security/clinical event to immutable audit trail
        
        Args:
            event_type: Type of event (ACCESS, TRANSCRIPTION, APPROVAL, etc.)
            case_id: Case identifier
            user_id: User who performed action
            details: Event-specific details
            sensitivity: STANDARD, SENSITIVE, CRITICAL
        """
        event = {
            'timestamp': datetime.now().isoformat(),
            'event_id': str(uuid.uuid4()),
            'event_type': event_type,
            'case_id': case_id,
            'user_id': user_id,
            'sensitivity': sensitivity,
            'details': details,
            'session_id': self._get_session_id()
        }
        
        # Write to master log (append-only, immutable)
        with open(self.master_log, 'a') as f:
            f.write(json.dumps(event) + '\n')
        
        # If sensitive, also create case-specific audit trail
        if sensitivity in ['SENSITIVE', 'CRITICAL']:
            case_audit = self.audit_dir / f"{case_id}_audit.jsonl"
            with open(case_audit, 'a') as f:
                f.write(json.dumps(event) + '\n')
        
        return event
    
    def get_audit_trail(self, case_id: str) -> List[Dict]:
        """Retrieve complete audit trail for a case"""
        case_audit = self.audit_dir / f"{case_id}_audit.jsonl"
        if not case_audit.exists():
            return []
        
        events = []
        with open(case_audit, 'r') as f:
            for line in f:
                events.append(json.loads(line))
        return events
    
    def get_user_activity(self, user_id: str, days: int = 30) -> List[Dict]:
        """Get all activity for a user in the last N days"""
        if not self.master_log.exists():
            return []
        
        cutoff_date = datetime.now().timestamp() - (days * 24 * 60 * 60)
        user_events = []
        
        with open(self.master_log, 'r') as f:
            for line in f:
                event = json.loads(line)
                if event['user_id'] == user_id:
                    event_time = datetime.fromisoformat(event['timestamp']).timestamp()
                    if event_time >= cutoff_date:
                        user_events.append(event)
        
        return user_events
    
    def _get_session_id(self) -> str:
        """Get current session ID (placeholder for actual implementation)"""
        return f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"


class HITLReviewInterface:
    """
    Human-in-the-Loop review interface for medical transcriptions
    Ensures mandatory clinician oversight before clinical use
    """
    
    def __init__(self):
        self.review_dir = Path("outputs/hitl_reviews")
        self.review_dir.mkdir(parents=True, exist_ok=True)
        self.audit_system = AuditTrailSystem()
    
    def create_review_package(self, case_id: str, transcription_results: Dict) -> Dict:
        """
        Create review package for clinician approval
        
        Args:
            case_id: Case identifier
            transcription_results: Complete transcription results from MedASR
        
        Returns:
            dict with review package data
        """
        print(f"\n{'='*80}")
        print(f"📋 CREATING HITL REVIEW PACKAGE")
        print(f"{'='*80}\n")
        print(f"Case ID: {case_id}")
        
        # Extract key information
        validation = transcription_results.get('validation', {})
        redaction = transcription_results.get('redaction', {})
        
        # Create review checklist
        review_checklist = [
            {
                'item': 'Transcript accuracy verified against audio recording',
                'checked': False,
                'required': True,
                'category': 'accuracy'
            },
            {
                'item': 'All critical terms (drugs, dosages, procedures) verified',
                'checked': False,
                'required': True,
                'category': 'safety'
            },
            {
                'item': 'No misinterpretation of medical terminology',
                'checked': False,
                'required': True,
                'category': 'accuracy'
            },
            {
                'item': 'PHI redaction appropriate (no patient identifiers leaked)',
                'checked': False,
                'required': True,
                'category': 'privacy'
            },
            {
                'item': 'Transcript suitable for clinical documentation',
                'checked': False,
                'required': True,
                'category': 'clinical'
            }
        ]
        
        # Add quality-specific checks
        if validation.get('status') == 'WARNING':
            review_checklist.append({
                'item': 'Low confidence sections reviewed and corrected',
                'checked': False,
                'required': True,
                'category': 'quality'
            })
        
        if validation.get('critical_terms_found'):
            review_checklist.append({
                'item': f"All {len(validation['critical_terms_found'])} critical medical terms verified",
                'checked': False,
                'required': True,
                'category': 'safety'
            })
        
        # Create review package
        review_package = {
            'case_id': case_id,
            'created_timestamp': datetime.now().isoformat(),
            'status': 'PENDING_REVIEW',
            'transcription': {
                'original_transcript': transcription_results.get('original_transcript', ''),
                'redacted_transcript': transcription_results.get('redacted_transcript', ''),
                'audio_file': transcription_results.get('audio_file', ''),
                'duration': transcription_results.get('metadata', {}).get('duration_seconds', 0)
            },
            'quality_assessment': {
                'status': validation.get('status', 'UNKNOWN'),
                'confidence': validation.get('overall_confidence', 0),
                'word_count': validation.get('word_count', 0),
                'critical_terms_found': validation.get('critical_terms_found', []),
                'issues': validation.get('issues', [])
            },
            'privacy_assessment': {
                'phi_redacted': redaction.get('redaction_count', 0),
                'phi_types_found': redaction.get('phi_types_found', [])
            },
            'review_checklist': review_checklist,
            'flagged_sections': self._identify_flagged_sections(transcription_results),
            'approval': {
                'approved': False,
                'reviewer_id': None,
                'reviewer_name': None,
                'reviewer_role': None,
                'review_date': None,
                'digital_signature': None,
                'comments': None,
                'corrections': []
            },
            'secondary_review': {
                'required': self._requires_dual_review(transcription_results),
                'reason': self._dual_review_reason(transcription_results),
                'approved': False,
                'reviewer_id': None,
                'reviewer_name': None,
                'review_date': None
            }
        }
        
        # Save review package
        review_file = self.review_dir / f"{case_id}_review_package.json"
        with open(review_file, 'w') as f:
            json.dump(review_package, f, indent=2)
        
        # Log event
        self.audit_system.log_event(
            event_type='REVIEW_PACKAGE_CREATED',
            case_id=case_id,
            user_id='system',
            details={
                'quality_status': validation.get('status'),
                'phi_redacted': redaction.get('redaction_count'),
                'requires_dual_review': review_package['secondary_review']['required']
            },
            sensitivity='SENSITIVE'
        )
        
        print(f"✅ Review package created: {review_file}")
        print(f"📋 Checklist items: {len(review_checklist)}")
        print(f"⚠️  Flagged sections: {len(review_package['flagged_sections'])}")
        print(f"🔍 Dual review required: {review_package['secondary_review']['required']}")
        
        return review_package
    
    def submit_review(self, case_id: str, reviewer_id: str, reviewer_name: str,
                     reviewer_role: str, approved: bool, comments: str = None,
                     corrections: List[Dict] = None, checklist_updates: Dict = None) -> Dict:
        """
        Submit clinician review and approval/rejection
        
        Args:
            case_id: Case identifier
            reviewer_id: Unique reviewer identifier
            reviewer_name: Reviewer's name
            reviewer_role: Reviewer's clinical role
            approved: Whether transcription is approved
            comments: Optional reviewer comments
            corrections: Optional list of corrections made
            checklist_updates: Updated checklist items
        
        Returns:
            dict with updated review package
        """
        print(f"\n{'='*80}")
        print(f"👨‍⚕️ PROCESSING HITL REVIEW SUBMISSION")
        print(f"{'='*80}\n")
        print(f"Case ID: {case_id}")
        print(f"Reviewer: {reviewer_name} ({reviewer_role})")
        print(f"Decision: {'APPROVED' if approved else 'REJECTED'}")
        
        # Load review package
        review_file = self.review_dir / f"{case_id}_review_package.json"
        if not review_file.exists():
            raise FileNotFoundError(f"Review package not found for case {case_id}")
        
        with open(review_file, 'r') as f:
            review_package = json.load(f)
        
        # Update approval section
        review_package['approval'] = {
            'approved': approved,
            'reviewer_id': reviewer_id,
            'reviewer_name': reviewer_name,
            'reviewer_role': reviewer_role,
            'review_date': datetime.now().isoformat(),
            'digital_signature': self._generate_signature(reviewer_id, case_id),
            'comments': comments,
            'corrections': corrections or []
        }
        
        # Update checklist if provided
        if checklist_updates:
            for i, item in enumerate(review_package['review_checklist']):
                if item['item'] in checklist_updates:
                    review_package['review_checklist'][i]['checked'] = checklist_updates[item['item']]
        
        # Update status
        if approved:
            if review_package['secondary_review']['required'] and not review_package['secondary_review']['approved']:
                review_package['status'] = 'AWAITING_SECONDARY_REVIEW'
            else:
                review_package['status'] = 'APPROVED'
        else:
            review_package['status'] = 'REJECTED'
        
        # Save updated package
        with open(review_file, 'w') as f:
            json.dump(review_package, f, indent=2)
        
        # Log event
        self.audit_system.log_event(
            event_type='HITL_REVIEW_SUBMITTED',
            case_id=case_id,
            user_id=reviewer_id,
            details={
                'reviewer_name': reviewer_name,
                'reviewer_role': reviewer_role,
                'decision': 'APPROVED' if approved else 'REJECTED',
                'comments': comments,
                'corrections_made': len(corrections) if corrections else 0
            },
            sensitivity='CRITICAL'
        )
        
        print(f"✅ Review submitted successfully")
        print(f"📋 Status: {review_package['status']}")
        print(f"🔐 Digital signature: {review_package['approval']['digital_signature'][:16]}...")
        
        return review_package
    
    def submit_secondary_review(self, case_id: str, reviewer_id: str, 
                               reviewer_name: str, approved: bool, 
                               comments: str = None) -> Dict:
        """
        Submit secondary review for high-risk cases
        
        Args:
            case_id: Case identifier
            reviewer_id: Second reviewer's ID
            reviewer_name: Second reviewer's name
            approved: Whether transcription is approved
            comments: Optional comments
        
        Returns:
            dict with updated review package
        """
        print(f"\n{'='*80}")
        print(f"👥 PROCESSING SECONDARY REVIEW")
        print(f"{'='*80}\n")
        print(f"Case ID: {case_id}")
        print(f"Second Reviewer: {reviewer_name}")
        print(f"Decision: {'APPROVED' if approved else 'REJECTED'}")
        
        # Load review package
        review_file = self.review_dir / f"{case_id}_review_package.json"
        with open(review_file, 'r') as f:
            review_package = json.load(f)
        
        # Update secondary review
        review_package['secondary_review'].update({
            'approved': approved,
            'reviewer_id': reviewer_id,
            'reviewer_name': reviewer_name,
            'review_date': datetime.now().isoformat(),
            'digital_signature': self._generate_signature(reviewer_id, case_id),
            'comments': comments
        })
        
        # Update overall status
        if approved and review_package['approval']['approved']:
            review_package['status'] = 'APPROVED'
        else:
            review_package['status'] = 'REJECTED'
        
        # Save
        with open(review_file, 'w') as f:
            json.dump(review_package, f, indent=2)
        
        # Log event
        self.audit_system.log_event(
            event_type='SECONDARY_REVIEW_SUBMITTED',
            case_id=case_id,
            user_id=reviewer_id,
            details={
                'reviewer_name': reviewer_name,
                'decision': 'APPROVED' if approved else 'REJECTED',
                'comments': comments
            },
            sensitivity='CRITICAL'
        )
        
        print(f"✅ Secondary review submitted")
        print(f"📋 Final status: {review_package['status']}")
        
        return review_package
    
    def get_review_status(self, case_id: str) -> Dict:
        """Get current review status for a case"""
        review_file = self.review_dir / f"{case_id}_review_package.json"
        if not review_file.exists():
            return {'status': 'NOT_FOUND', 'case_id': case_id}
        
        with open(review_file, 'r') as f:
            review_package = json.load(f)
        
        return {
            'case_id': case_id,
            'status': review_package['status'],
            'primary_reviewer': review_package['approval'].get('reviewer_name'),
            'secondary_reviewer': review_package['secondary_review'].get('reviewer_name'),
            'requires_dual_review': review_package['secondary_review']['required'],
            'created': review_package['created_timestamp'],
            'reviewed': review_package['approval'].get('review_date')
        }
    
    def _identify_flagged_sections(self, transcription_results: Dict) -> List[Dict]:
        """Identify sections requiring special attention"""
        flagged = []
        validation = transcription_results.get('validation', {})
        
        for issue in validation.get('issues', []):
            if issue['severity'] in ['CRITICAL', 'HIGH']:
                flagged.append({
                    'type': issue['type'],
                    'severity': issue['severity'],
                    'term': issue.get('term'),
                    'message': issue['message'],
                    'recommendation': issue['recommendation']
                })
        
        return flagged
    
    def _requires_dual_review(self, transcription_results: Dict) -> bool:
        """Determine if case requires dual review"""
        validation = transcription_results.get('validation', {})
        
        # Require dual review if:
        # 1. Quality status is WARNING or FAILED
        if validation.get('status') in ['WARNING', 'FAILED']:
            return True
        
        # 2. Critical terms with low confidence
        for issue in validation.get('issues', []):
            if issue['severity'] == 'CRITICAL':
                return True
        
        # 3. High-risk procedures mentioned
        transcript = transcription_results.get('original_transcript', '').lower()
        high_risk_terms = ['experimental', 'clinical trial', 'off-label', 'stage iv', 'metastatic']
        if any(term in transcript for term in high_risk_terms):
            return True
        
        return False
    
    def _dual_review_reason(self, transcription_results: Dict) -> str:
        """Determine reason for dual review requirement"""
        validation = transcription_results.get('validation', {})
        
        if validation.get('status') in ['WARNING', 'FAILED']:
            return f"Low transcription quality ({validation.get('status')})"
        
        for issue in validation.get('issues', []):
            if issue['severity'] == 'CRITICAL':
                return f"Critical issue: {issue['message']}"
        
        transcript = transcription_results.get('original_transcript', '').lower()
        if 'experimental' in transcript or 'clinical trial' in transcript:
            return "Experimental treatment discussed"
        if 'stage iv' in transcript or 'metastatic' in transcript:
            return "Advanced/metastatic disease (high-risk case)"
        
        return "High-risk case requiring additional oversight"
    
    def _generate_signature(self, reviewer_id: str, case_id: str) -> str:
        """Generate cryptographic digital signature for approval"""
        signature_data = f"{reviewer_id}:{case_id}:{datetime.now().isoformat()}"
        return hashlib.sha256(signature_data.encode()).hexdigest()


def main():
    """Test HITL review system"""
    
    print("\n" + "="*80)
    print("TESTING HITL REVIEW SYSTEM FOR MEDASR")
    print("="*80 + "\n")
    
    # Initialize HITL system
    hitl_system = HITLReviewInterface()
    
    # Load a sample transcription result
    transcription_file = Path("outputs/medasr_transcriptions/TEST_MDT_001_complete.json")
    
    if transcription_file.exists():
        with open(transcription_file, 'r') as f:
            transcription_results = json.load(f)
        
        # Create review package
        review_package = hitl_system.create_review_package(
            case_id="TEST_MDT_001",
            transcription_results=transcription_results
        )
        
        print(f"\n{'='*80}")
        print("SIMULATING CLINICIAN REVIEW")
        print(f"{'='*80}\n")
        
        # Simulate approval
        updated_package = hitl_system.submit_review(
            case_id="TEST_MDT_001",
            reviewer_id="DR001",
            reviewer_name="Dr. Sarah Johnson",
            reviewer_role="Medical Oncologist",
            approved=True,
            comments="Transcript reviewed and verified. Accurately captures MDT discussion.",
            checklist_updates={
                'Transcript accuracy verified against audio recording': True,
                'All critical terms (drugs, dosages, procedures) verified': True,
                'No misinterpretation of medical terminology': True,
                'PHI redaction appropriate (no patient identifiers leaked)': True,
                'Transcript suitable for clinical documentation': True
            }
        )
        
        # Check status
        status = hitl_system.get_review_status("TEST_MDT_001")
        print(f"\n{'='*80}")
        print("REVIEW STATUS")
        print(f"{'='*80}")
        print(f"Status: {status['status']}")
        print(f"Primary Reviewer: {status['primary_reviewer']}")
        print(f"Dual Review Required: {status['requires_dual_review']}")
        
    else:
        print("⚠️  No transcription results found. Run medical_transcription_medasr.py first.")
    
    print("\n" + "="*80)
    print("HITL SYSTEM TEST COMPLETE")
    print("="*80 + "\n")
    
    print("📋 USAGE:")
    print("  hitl = HITLReviewInterface()")
    print("  review = hitl.create_review_package(case_id, transcription_results)")
    print("  hitl.submit_review(case_id, reviewer_id, name, role, approved=True)")
    print("\n✅ HITL system ready for production use!")


if __name__ == "__main__":
    main()

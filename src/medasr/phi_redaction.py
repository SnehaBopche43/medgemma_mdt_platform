"""PHI Redaction System for HIPAA Compliance"""

import re
from datetime import datetime

class PHIRedactor:
    def __init__(self):
        print("🔒 Initializing PHI Redaction...")
        self.patterns = {
            'date': r'\b(?:\d{1,2}/\d{1,2}/\d{4}|\w+ \d{1,2},? \d{4})\b',
            'mrn': r'\b(?:MRN|Medical Record)[:\s]+[\d-]+\b',
            'phone': r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',
            'ssn': r'\b\d{3}-\d{2}-\d{4}\b',
            'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
        }
        print("✅ PHI Redaction ready\n")
    
    def redact(self, transcript):
        print("🔒 Redacting PHI...")
        redacted = transcript
        redaction_count = 0
        redaction_map = {}
        
        for phi_type, pattern in self.patterns.items():
            matches = re.findall(pattern, redacted, re.IGNORECASE)
            for match in matches:
                redaction_count += 1
                pseudonym = f"[{phi_type.upper()}-{redaction_count:03d}]"
                redaction_map[pseudonym] = {'original': match, 'type': phi_type}
                redacted = redacted.replace(match, pseudonym, 1)
        
        print(f"✅ Redacted {redaction_count} PHI items\n")
        
        return {
            'redacted_transcript': redacted,
            'original_transcript': transcript,
            'redaction_count': redaction_count,
            'redaction_map': redaction_map
        }

if __name__ == "__main__":
    print("="*80)
    print("TESTING PHI REDACTION")
    print("="*80)
    redactor = PHIRedactor()
    result = redactor.redact("Patient MRN: 12345, DOB: 01/15/1965, Phone: 555-123-4567")
    print(f"Redacted: {result['redacted_transcript']}")
    print(f"Items: {result['redaction_count']}")
    print("="*80)

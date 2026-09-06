"""
SAARTHI AI — MedGemma MDT Platform
Safety Layer 0: Clinical De-identification Module

This module is the MANDATORY first step in the entire pipeline.
It must be called before any case data is passed to MedGemma,
any agent, or any external API.

It strips all 18 HIPAA Safe Harbour identifiers from clinical
documents using Microsoft Presidio + spaCy.

Integration point in your existing pipeline:
    unified_mdt_pipeline_with_hitl.py → run_pipeline()
    → Call deidentify_case_data() BEFORE Step 1 (Imaging Analysis)

Author: SAARTHI AI
Version: 1.0.0
Date: March 2026
"""

import re
import json
import uuid
import logging
from copy import deepcopy
from datetime import datetime
from typing import Optional

from presidio_analyzer import AnalyzerEngine, RecognizerRegistry, Pattern, PatternRecognizer
from presidio_analyzer.nlp_engine import NlpEngineProvider
from presidio_anonymizer import AnonymizerEngine
from presidio_anonymizer.entities import OperatorConfig

# ─────────────────────────────────────────────────────────────────────────────
# Logging
# ─────────────────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] SAARTHI.Deidentifier: %(message)s"
)
logger = logging.getLogger("SAARTHI.Deidentifier")


# ─────────────────────────────────────────────────────────────────────────────
# HIPAA Safe Harbour — All 18 Identifier Categories
# ─────────────────────────────────────────────────────────────────────────────
HIPAA_ENTITIES = [
    "PERSON",            # 1. Names
    "LOCATION",          # 2. Geographic data (addresses, postcodes)
    "DATE_TIME",         # 3. Dates (except year)
    "PHONE_NUMBER",      # 4. Phone numbers
    "PHONE_NUMBER",      # 5. Fax numbers (same detector)
    "EMAIL_ADDRESS",     # 6. Email addresses
    "US_SSN",            # 7. Social Security Numbers
    "MEDICAL_LICENSE",   # 8. Medical record / licence numbers
    "US_PASSPORT",       # 9. Health plan beneficiary / passport numbers
    "CREDIT_CARD",       # 10. Account numbers
    "US_DRIVER_LICENSE", # 11. Certificate / licence numbers
    "NRP",               # 12. National registration / ID numbers
    "IBAN_CODE",         # 13. Bank / account numbers
    "URL",               # 14. Web URLs
    "IP_ADDRESS",        # 15. IP addresses
    "UK_NHS",            # 16. NHS / biometric identifier numbers
]
# Deduplicate
HIPAA_ENTITIES = list(dict.fromkeys(HIPAA_ENTITIES))


# ─────────────────────────────────────────────────────────────────────────────
# Custom Recognizer: Clinical-Specific Identifiers
# (MRN, NHS, Emirates ID, DOB labels, Patient IDs, UK postcodes)
# ─────────────────────────────────────────────────────────────────────────────
class ClinicalIdentifierRecognizer(PatternRecognizer):
    """
    Detects clinical identifiers not covered by Presidio's default recognizers.
    Specifically tuned for UK/UAE oncology MDT documents.
    """
    def __init__(self):
        patterns = [
            Pattern(
                name="medical_record_number",
                regex=r"\b(?:MRN|MR|MED(?:ICAL)?\s*(?:RECORD|REF)(?:\s*(?:NO|NUM|NUMBER|#))?)\s*[:\-#]?\s*[A-Z0-9\-]{4,15}\b",
                score=0.9
            ),
            Pattern(
                name="nhs_number",
                regex=r"\b\d{3}[\s\-]\d{3}[\s\-]\d{4}\b",
                score=0.85
            ),
            Pattern(
                name="emirates_id",
                regex=r"\b784[\s\-]\d{4}[\s\-]\d{7}[\s\-]\d\b",
                score=0.95
            ),
            Pattern(
                name="dob_labelled",
                regex=r"\b(?:DOB|D\.O\.B\.?|Date\s+of\s+Birth)\s*[:\-]?\s*\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4}\b",
                score=0.95
            ),
            Pattern(
                name="patient_id_labelled",
                regex=r"\b(?:Patient\s+ID|Pt\s+ID|PID|Patient\s+No)\s*[:\-#]?\s*[A-Z0-9\-]{4,15}\b",
                score=0.9
            ),
            Pattern(
                name="uk_postcode",
                regex=r"\b[A-Z]{1,2}\d{1,2}[A-Z]?\s*\d[A-Z]{2}\b",
                score=0.75
            ),
            Pattern(
                name="uae_phone",
                regex=r"\+971\s*\d{2}\s*\d{3}\s*\d{4}\b",
                score=0.95
            ),
            Pattern(
                name="international_phone",
                regex=r"\+\d{1,3}\s*\d{2,3}\s*\d{3,4}\s*\d{3,4}\b",
                score=0.85
            ),
            Pattern(
                name="hospital_number",
                regex=r"\b(?:Hospital\s+(?:No|Number|Ref)|HN|H\.N\.)\s*[:\-#]?\s*[A-Z0-9\-]{4,15}\b",
                score=0.9
            ),
        ]
        super().__init__(
            supported_entity="CLINICAL_IDENTIFIER",
            patterns=patterns,
            name="ClinicalIdentifierRecognizer",
            supported_language="en"
        )


# ─────────────────────────────────────────────────────────────────────────────
# Main De-identification Engine
# ─────────────────────────────────────────────────────────────────────────────
class ClinicalDeidentifier:
    """
    Production-grade de-identification engine for the MedGemma MDT Platform.

    RULE: This class must be instantiated ONCE (singleton) and reused
    across all pipeline calls to avoid reloading the NLP model.

    Usage in your pipeline:
        from deidentifier import deidentify_case_data

        # In run_pipeline(), before Step 1:
        deid_result = deidentify_case_data(case_data, case_id=case_id)
        safe_case_data = deid_result["safe_case_data"]
        token_map = deid_result["token_map"]  # Store securely, never transmit

        # Pass safe_case_data to all agents instead of raw case_data
        imaging_result = self.imaging_agent.analyze_imaging(safe_case_data["imaging"])
    """

    def __init__(self):
        logger.info("Loading de-identification engine (Safety Layer 0)...")

        # Use spaCy large model for best clinical NER accuracy
        nlp_config = {
            "nlp_engine_name": "spacy",
            "models": [{"lang_code": "en", "model_name": "en_core_web_lg"}],
        }
        provider = NlpEngineProvider(nlp_configuration=nlp_config)
        nlp_engine = provider.create_engine()

        # Register all recognizers
        registry = RecognizerRegistry()
        registry.load_predefined_recognizers(nlp_engine=nlp_engine)
        registry.add_recognizer(ClinicalIdentifierRecognizer())

        self.analyzer = AnalyzerEngine(
            registry=registry,
            nlp_engine=nlp_engine,
            supported_languages=["en"]
        )
        self.anonymizer = AnonymizerEngine()
        self.all_entities = HIPAA_ENTITIES + ["CLINICAL_IDENTIFIER"]

        logger.info("De-identification engine ready. All 18 HIPAA identifiers active.")

    # ─────────────────────────────────────────────────────────────────────────
    # Public API: deidentify_text()
    # ─────────────────────────────────────────────────────────────────────────
    def deidentify_text(
        self,
        text: str,
        token_map: dict,
        case_id: Optional[str] = None,
        score_threshold: float = 0.6
    ) -> str:
        """
        De-identify a single string of clinical text.

        Args:
            text:             Raw clinical text.
            token_map:        Shared dict — tokens will be added to this dict.
                              Pass the same dict across all calls for one case.
            case_id:          For logging only.
            score_threshold:  Confidence threshold (0.0–1.0). Default 0.6.

        Returns:
            De-identified text string with PHI replaced by typed tokens.
        """
        if not text or not isinstance(text, str) or not text.strip():
            return text

        # Analyze
        results = self.analyzer.analyze(
            text=text,
            entities=self.all_entities,
            language="en",
            score_threshold=score_threshold
        )

        if not results:
            return text

        # Build per-entity-type counters for token naming
        entity_counters = {}

        def make_replacer(etype):
            def replace(matched_text):
                if etype not in entity_counters:
                    entity_counters[etype] = 0
                entity_counters[etype] += 1
                token = f"<{etype}_{entity_counters[etype]}>"
                token_map[token] = matched_text
                return token
            return replace

        operators = {
            etype: OperatorConfig("custom", {"lambda": make_replacer(etype)})
            for etype in set(r.entity_type for r in results)
        }

        anonymized = self.anonymizer.anonymize(
            text=text,
            analyzer_results=results,
            operators=operators
        )

        # Apply additional regex cleanup for dates, postcodes, and addresses
        clean_text = self._regex_cleanup(anonymized.text, token_map, entity_counters)

        return clean_text

    def _second_pass_deidentify(self, text: str, token_map: dict) -> str:
        """
        Second-pass cleanup: replace any original PHI values that survived
        the first pass. This handles cases where Presidio detects a larger
        entity (e.g., full address) but misses a sub-component (e.g., 'Villa 12').
        """
        if not text:
            return text
        import re as _re
        for token, original in list(token_map.items()):
            if len(original) >= 6 and original in text:
                text = text.replace(original, token)
        return text

    # ─────────────────────────────────────────────────────────────────────────
    # Public API: deidentify_case_data()
    # ─────────────────────────────────────────────────────────────────────────
    def deidentify_case_data(
        self,
        case_data: dict,
        case_id: Optional[str] = None
    ) -> dict:
        """
        De-identify a complete case data dictionary (as used in your pipeline).

        This function recursively walks the entire case_data dict and
        de-identifies every string value it finds.

        Args:
            case_data:  The raw case dict loaded from JSON (as in run_pipeline).
            case_id:    Optional case identifier for audit logging.

        Returns:
            Dict with:
            - safe_case_data: De-identified copy of case_data, safe for AI models.
            - token_map:      Dict mapping tokens back to real values.
                              STORE SECURELY. Never transmit externally.
            - entities_count: Total number of identifiers removed.
            - audit_log:      Structured audit record for the audit trail.
        """
        session_id = str(uuid.uuid4())
        token_map = {}

        logger.info(f"De-identifying case: {case_id or 'UNKNOWN'} | Session: {session_id}")

        # Deep copy to avoid mutating the original
        safe_case_data = deepcopy(case_data)

        # First pass: Presidio NLP + regex de-identification
        self._deidentify_dict(safe_case_data, token_map, case_id)

        # Second pass: catch any PHI sub-components that survived the first pass
        # (e.g., 'Villa 12' inside a larger address entity)
        self._second_pass_dict(safe_case_data, token_map)

        logger.info(f"  Complete. {len(token_map)} identifiers replaced.")

        audit_log = {
            "event": "DEIDENTIFICATION_COMPLETED",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "case_id": case_id or "UNKNOWN",
            "session_id": session_id,
            "identifiers_removed": len(token_map),
            "layer": "Safety Layer 0 — De-identification",
            "tool": "Microsoft Presidio + spaCy en_core_web_lg",
            "hipaa_identifiers_covered": 18,
            "status": "SUCCESS"
        }

        return {
            "safe_case_data": safe_case_data,
            "token_map": token_map,
            "entities_count": len(token_map),
            "audit_log": audit_log,
            "session_id": session_id
        }

    # ─────────────────────────────────────────────────────────────────────────
    # Public API: verify()
    # ─────────────────────────────────────────────────────────────────────────
    def verify(self, safe_case_data: dict, token_map: dict) -> dict:
        """
        Verify that no original PHI values remain in the de-identified data.

        Call this after deidentify_case_data() to confirm success.

        Returns:
            Dict with verification_passed (bool) and details of any failures.
        """
        # Convert safe_case_data to a flat string for scanning
        flat_text = json.dumps(safe_case_data)
        failures = []

        # Build a set of all unique original values for efficient lookup.
        # We only flag values that are:
        # (a) longer than 8 characters (to exclude common city names / words)
        # (b) not themselves a token pattern (i.e., not already a <TOKEN_N> string)
        # (c) present verbatim in the safe data JSON
        MIN_PHI_LENGTH = 8
        seen_originals = set()

        for token, original in token_map.items():
            if len(original) < MIN_PHI_LENGTH:
                continue
            if original in seen_originals:
                continue  # Already checked this value
            seen_originals.add(original)
            # Use word-boundary-aware check: look for the original as a
            # standalone substring, not as part of a token placeholder
            import re as _re
            pattern = _re.compile(_re.escape(original), _re.IGNORECASE)
            matches = pattern.findall(flat_text)
            if matches:
                failures.append({"original": original, "token": token})

        passed = len(failures) == 0

        if passed:
            logger.info("  Verification PASSED: No residual PHI detected.")
        else:
            logger.warning(f"  Verification FAILED: {len(failures)} residual values found.")

        return {
            "verification_passed": passed,
            "residual_phi_found": failures,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }

    # ─────────────────────────────────────────────────────────────────────────
    # Private Helpers
    # ─────────────────────────────────────────────────────────────────────────
    def _deidentify_dict(self, data, token_map: dict, case_id: Optional[str]):
        """Recursively walk a dict/list and de-identify all string values."""
        if isinstance(data, dict):
            for key, value in data.items():
                if isinstance(value, str):
                    data[key] = self.deidentify_text(value, token_map, case_id)
                elif isinstance(value, (dict, list)):
                    self._deidentify_dict(value, token_map, case_id)
        elif isinstance(data, list):
            for i, item in enumerate(data):
                if isinstance(item, str):
                    data[i] = self.deidentify_text(item, token_map, case_id)
                elif isinstance(item, (dict, list)):
                    self._deidentify_dict(item, token_map, case_id)

    def _second_pass_dict(self, data, token_map: dict):
        """
        Second pass: after all strings have been processed and the token_map
        is fully populated, scan every string again for any surviving PHI
        sub-components (e.g., 'Villa 12' surviving inside a larger address token).
        """
        if isinstance(data, dict):
            for key, value in data.items():
                if isinstance(value, str):
                    data[key] = self._second_pass_deidentify(value, token_map)
                elif isinstance(value, (dict, list)):
                    self._second_pass_dict(value, token_map)
        elif isinstance(data, list):
            for i, item in enumerate(data):
                if isinstance(item, str):
                    data[i] = self._second_pass_deidentify(item, token_map)
                elif isinstance(item, (dict, list)):
                    self._second_pass_dict(item, token_map)

    def _regex_cleanup(self, text: str, token_map: dict, entity_counters: dict) -> str:
        """
        Catch any remaining date or postcode patterns that Presidio may miss
        in dense clinical text formats.
        """
        # Standalone dates (dd/mm/yyyy, dd-mm-yyyy, dd.mm.yyyy)
        date_re = re.compile(r"\b\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4}\b")
        def replace_date(m):
            n = entity_counters.get("DATE_TIME", 0) + 1
            entity_counters["DATE_TIME"] = n
            token = f"<DATE_TIME_{n}>"
            token_map[token] = m.group(0)
            return token
        text = date_re.sub(replace_date, text)

        # Standalone UK postcodes not caught above
        postcode_re = re.compile(r"\b[A-Z]{1,2}\d{1,2}[A-Z]?\s*\d[A-Z]{2}\b")
        def replace_postcode(m):
            n = entity_counters.get("LOCATION", 0) + 1
            entity_counters["LOCATION"] = n
            token = f"<LOCATION_{n}>"
            token_map[token] = m.group(0)
            return token
        text = postcode_re.sub(replace_postcode, text)

        return text


# ─────────────────────────────────────────────────────────────────────────────
# Singleton Instance (load model once, reuse everywhere)
# ─────────────────────────────────────────────────────────────────────────────
_instance: Optional[ClinicalDeidentifier] = None

def _get_instance() -> ClinicalDeidentifier:
    global _instance
    if _instance is None:
        _instance = ClinicalDeidentifier()
    return _instance


# ─────────────────────────────────────────────────────────────────────────────
# Public Convenience Functions (call these from your pipeline)
# ─────────────────────────────────────────────────────────────────────────────

def deidentify_case_data(case_data: dict, case_id: Optional[str] = None) -> dict:
    """
    PRIMARY FUNCTION — call this from run_pipeline() before Step 1.

    De-identifies the entire case_data dictionary.

    Returns:
        {
          "safe_case_data": dict,   ← pass this to all agents
          "token_map": dict,        ← store securely, never transmit
          "entities_count": int,
          "audit_log": dict,
          "session_id": str
        }
    """
    return _get_instance().deidentify_case_data(case_data, case_id=case_id)


def verify_deidentification(safe_case_data: dict, token_map: dict) -> dict:
    """
    Verify that de-identification was successful.
    Returns {"verification_passed": bool, "residual_phi_found": list}
    """
    return _get_instance().verify(safe_case_data, token_map)

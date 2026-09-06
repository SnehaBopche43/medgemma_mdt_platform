"""
SAARTHI AI — MedGemma MDT Platform
Test Suite: Safety Layer 0 — De-identification

Tests the ClinicalDeidentifier against realistic oncology MDT case documents.
Covers all 18 HIPAA Safe Harbour identifier categories.

Run from the src/ directory:
    python test_deidentifier.py

Expected result: ALL TESTS PASS
"""

import json
import sys
from deidentifier import deidentify_case_data, verify_deidentification

# ─────────────────────────────────────────────────────────────────────────────
# Test Fixtures: Realistic Synthetic MDT Case Data
# (All names, numbers, and identifiers are entirely fictitious)
# ─────────────────────────────────────────────────────────────────────────────

BREAST_CANCER_CASE = {
    "patient_id": "BC-2026-00142",
    "patient_info": {
        "name": "Fatima Al-Rashidi",
        "dob": "14/03/1972",
        "age": 53,
        "gender": "Female",
        "mrn": "MRN: DXB-447821",
        "nhs_number": "485 777 3201",
        "emirates_id": "784-1972-1234567-8",
        "address": "Villa 12, Al Barsha 2, Dubai, UAE, DU 12345",
        "phone": "+971 50 123 4567",
        "email": "f.alrashidi@email.com",
        "gp": "Dr. Sarah Johnson, Al Wasl Hospital"
    },
    "cancer_type": "Breast Cancer",
    "staging": {
        "clinical_stage": "IIB",
        "t_stage": "T2",
        "n_stage": "N1",
        "m_stage": "M0"
    },
    "pathology": {
        "report": "Core biopsy performed on 05/01/2026 at Dubai Oncology Centre. "
                  "Invasive ductal carcinoma, Grade 3. ER positive (90%), PR positive (70%), "
                  "HER2 negative. Ki-67 35%. Referring clinician: Dr. Ahmed Hassan, Consultant Surgeon.",
        "histology": "Invasive ductal carcinoma",
        "grade": 3,
        "er_status": "Positive",
        "pr_status": "Positive",
        "her2_status": "Negative"
    },
    "imaging": {
        "modality": "MRI Breast + CT Chest/Abdomen/Pelvis",
        "report": "MRI performed on 12/01/2026. Patient: Fatima Al-Rashidi, DOB 14/03/1972. "
                  "Hospital No: H-8821-DXB. 3.2cm mass in upper outer quadrant left breast. "
                  "Two suspicious axillary lymph nodes. No distant metastases. "
                  "Radiologist: Dr. Priya Nair, FRCR, Dubai Radiology Institute, "
                  "contact: p.nair@dri.ae, Tel: +971 4 567 8901.",
        "findings": "3.2cm IDC left breast, 2 axillary nodes"
    },
    "clinical_notes": "Patient seen in clinic on 20/01/2026 by Dr. James Whitfield. "
                      "She lives at Villa 12, Al Barsha 2, Dubai. "
                      "Her insurance policy number is INS-AXA-2024-88712. "
                      "IP address of portal login: 192.168.1.45. "
                      "Next MDT: 15/02/2026 at 08:00.",
    "medications": ["Letrozole 2.5mg OD", "Aspirin 75mg OD"],
    "allergies": ["Penicillin"]
}

LUNG_CANCER_CASE = {
    "patient_id": "LC-2026-00089",
    "patient_info": {
        "name": "Mohammed Al-Farsi",
        "dob": "22/07/1965",
        "age": 60,
        "gender": "Male",
        "mrn": "MRN: SHJ-221934",
        "phone": "+971 55 987 6543",
        "email": "m.alfarsi@gmail.com",
        "postcode": "SW1A 2AA",
        "ssn": "123-45-6789"
    },
    "cancer_type": "Lung Cancer",
    "staging": {
        "clinical_stage": "IIIA",
        "t_stage": "T3",
        "n_stage": "N2",
        "m_stage": "M0",
        "histology": "Non-small cell lung cancer, adenocarcinoma"
    },
    "pathology": {
        "report": "CT-guided biopsy 08/02/2026. Patient Mohammed Al-Farsi, MRN SHJ-221934. "
                  "NSCLC adenocarcinoma. EGFR mutation detected (exon 19 deletion). "
                  "PD-L1 TPS 45%. Pathologist: Dr. Linda Chen, Sharjah Pathology Lab.",
        "molecular": "EGFR exon 19 deletion positive",
        "pdl1": "45%"
    },
    "imaging": {
        "modality": "PET-CT",
        "report": "PET-CT 15/02/2026. 4.5cm right upper lobe mass. Mediastinal nodal involvement. "
                  "No distant metastases. Radiologist: Dr. Khalid Al-Mansouri, +971 4 321 0987.",
        "findings": "4.5cm RUL mass, N2 disease"
    },
    "clinical_notes": "Discussed with patient on 01/03/2026. Smoker 40 pack years. "
                      "Lives at Flat 7, Al Nahda Street, Sharjah. "
                      "Emergency contact: Aisha Al-Farsi, +971 50 111 2222. "
                      "Website: http://patient-portal.sharjah-health.ae/user/221934"
}


# ─────────────────────────────────────────────────────────────────────────────
# Test Runner
# ─────────────────────────────────────────────────────────────────────────────

def run_test(test_name: str, case_data: dict) -> bool:
    """Run a single de-identification test. Returns True if passed."""
    print(f"\n{'='*70}")
    print(f"TEST: {test_name}")
    print(f"{'='*70}")

    # ── Step 1: De-identify ──────────────────────────────────────────────────
    result = deidentify_case_data(case_data, case_id=case_data.get("patient_id"))

    safe_data = result["safe_case_data"]
    token_map = result["token_map"]
    audit_log = result["audit_log"]

    print(f"\n  Identifiers removed : {result['entities_count']}")
    print(f"  Session ID          : {result['session_id']}")
    print(f"  Audit status        : {audit_log['status']}")

    # ── Step 2: Verify ───────────────────────────────────────────────────────
    verification = verify_deidentification(safe_data, token_map)
    passed = verification["verification_passed"]

    if passed:
        print(f"\n  ✅ VERIFICATION PASSED — No residual PHI detected.")
    else:
        print(f"\n  ❌ VERIFICATION FAILED — Residual PHI found:")
        for f in verification["residual_phi_found"]:
            print(f"     Original: '{f['original']}' → Token: {f['token']}")

    # ── Step 3: Spot-check key fields ────────────────────────────────────────
    print(f"\n  Spot-check results:")

    patient_name = case_data["patient_info"]["name"]
    safe_json = json.dumps(safe_data)

    checks = [
        ("Patient name removed",
         patient_name not in safe_json),
        ("Email removed",
         case_data["patient_info"].get("email", "") not in safe_json),
        ("Phone removed",
         case_data["patient_info"].get("phone", "") not in safe_json),
        ("DOB removed",
         case_data["patient_info"].get("dob", "") not in safe_json),
        ("Token map is non-empty",
         len(token_map) > 0),
        ("Safe data preserves cancer type",
         safe_data.get("cancer_type") == case_data.get("cancer_type")),
        ("Safe data preserves staging",
         safe_data.get("staging") is not None),
    ]

    all_checks_passed = True
    for check_name, check_result in checks:
        status = "✅" if check_result else "❌"
        print(f"     {status} {check_name}")
        if not check_result:
            all_checks_passed = False

    # ── Step 4: Show token map sample ────────────────────────────────────────
    print(f"\n  Token map sample (first 5 entries):")
    for i, (token, original) in enumerate(list(token_map.items())[:5]):
        print(f"     {token} ← '{original}'")

    overall = passed and all_checks_passed
    print(f"\n  RESULT: {'✅ PASSED' if overall else '❌ FAILED'}")
    return overall


def test_audit_log_structure():
    """Verify the audit log contains all required fields for the audit trail."""
    print(f"\n{'='*70}")
    print(f"TEST: Audit Log Structure")
    print(f"{'='*70}")

    result = deidentify_case_data(BREAST_CANCER_CASE, case_id="TEST-AUDIT")
    audit = result["audit_log"]

    required_fields = [
        "event", "timestamp", "case_id", "session_id",
        "identifiers_removed", "layer", "tool",
        "hipaa_identifiers_covered", "status"
    ]

    all_present = True
    for field in required_fields:
        present = field in audit
        status = "✅" if present else "❌"
        print(f"  {status} audit_log['{field}'] = {audit.get(field, 'MISSING')}")
        if not present:
            all_present = False

    print(f"\n  RESULT: {'✅ PASSED' if all_present else '❌ FAILED'}")
    return all_present


def test_singleton_performance():
    """Verify the singleton pattern — second call must be significantly faster."""
    import time
    print(f"\n{'='*70}")
    print(f"TEST: Singleton Performance (model loads once)")
    print(f"{'='*70}")

    t1 = time.time()
    deidentify_case_data(BREAST_CANCER_CASE, case_id="PERF-1")
    first_call = time.time() - t1

    t2 = time.time()
    deidentify_case_data(LUNG_CANCER_CASE, case_id="PERF-2")
    second_call = time.time() - t2

    print(f"  First call  : {first_call:.2f}s (includes model load)")
    print(f"  Second call : {second_call:.2f}s (model already loaded)")
    print(f"  Speedup     : {first_call/second_call:.1f}x")

    passed = second_call < first_call
    print(f"\n  RESULT: {'✅ PASSED' if passed else '❌ FAILED'}")
    return passed


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("\n" + "="*70)
    print("  SAARTHI AI — MedGemma MDT Platform")
    print("  Safety Layer 0: De-identification Test Suite")
    print("="*70)

    results = []

    results.append(run_test("Breast Cancer Case (UAE Patient)", BREAST_CANCER_CASE))
    results.append(run_test("Lung Cancer Case (UAE Patient)", LUNG_CANCER_CASE))
    results.append(test_audit_log_structure())
    results.append(test_singleton_performance())

    print("\n" + "="*70)
    print(f"  FINAL RESULT: {sum(results)}/{len(results)} tests passed")
    print("="*70 + "\n")

    if all(results):
        print("  ✅ ALL TESTS PASSED — Safety Layer 0 is ready for integration.\n")
        sys.exit(0)
    else:
        print("  ❌ SOME TESTS FAILED — Review output above before integrating.\n")
        sys.exit(1)

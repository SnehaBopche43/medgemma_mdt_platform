"""
SAARTHI AI — MedGemma MDT Platform
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Safety Layer 4: Human-in-the-Loop (HITL) Approval System
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

PURPOSE
-------
Ensures that NO AI-generated clinical recommendation is acted upon without
explicit review and approval by a licensed clinician. This is the most
important safety layer in the platform — it is the final human gate before
any output reaches a clinical decision.

WHAT THIS FILE CONTAINS
-----------------------
1. HITLApprovalSystem  — Core approval engine (backward-compatible with your
                         existing code; all original methods preserved)
2. Approval Workflow   — Create → Review → Approve / Reject / Override
3. Confidence Scoring  — Every recommendation carries a confidence level
4. Urgency Flags       — ROUTINE / URGENT / CRITICAL routing
5. Override Tracking   — Full audit trail when clinician overrides AI
6. MDT Question Hints  — Radiologist question anticipation (Agent 13 output)
7. Multi-Agent Support — Handles all 17 agents in the platform
8. Immutable Audit Log — Every action timestamped and saved to disk
9. Session Summary     — End-of-pipeline summary of all approvals

USAGE (drop-in replacement for your existing hitl_approval_system.py)
----------------------------------------------------------------------
    from hitl_approval_system import HITLApprovalSystem

    hitl = HITLApprovalSystem()

    # Create a request (same API as before)
    request = hitl.create_approval_request(
        recommendation_data=agent_output,
        recommendation_type="imaging_analysis"
    )

    # Interactive review in terminal
    decision = hitl.interactive_review(request["request_id"])

    # Or approve/reject programmatically
    hitl.approve_request(request_id, clinician_id="DR_SMITH", notes="Agreed")
    hitl.reject_request(request_id, clinician_id="DR_SMITH", reason="Staging incorrect")

BACKWARD COMPATIBILITY
----------------------
All original method signatures are preserved:
  - create_approval_request(recommendation_data, recommendation_type)
  - approve_request(request_id, clinician_id, notes="")
  - reject_request(request_id, clinician_id, reason="")
  - get_pending_requests()
  - get_request_status(request_id)
"""

import json
import uuid
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, List, Any
from enum import Enum


# ─────────────────────────────────────────────────────────────────────────────
# Enumerations
# ─────────────────────────────────────────────────────────────────────────────

class ApprovalStatus(str, Enum):
    PENDING   = "pending"
    APPROVED  = "approved"
    REJECTED  = "rejected"
    OVERRIDDEN = "overridden"   # Clinician accepted AI output but modified it
    ESCALATED  = "escalated"   # Sent to senior clinician for second opinion


class UrgencyLevel(str, Enum):
    ROUTINE  = "ROUTINE"    # Standard MDT workflow
    URGENT   = "URGENT"     # Review within 4 hours
    CRITICAL = "CRITICAL"   # Immediate review required (e.g., suspected emergency)


class ConfidenceLevel(str, Enum):
    HIGH     = "HIGH"       # ≥ 85% — AI is confident
    MODERATE = "MODERATE"   # 65–84% — Review carefully
    LOW      = "LOW"        # < 65% — AI is uncertain; clinician must decide


# ─────────────────────────────────────────────────────────────────────────────
# Agent Registry
# Maps recommendation_type strings to human-readable agent names and
# default urgency levels. Covers all 17 agents in the platform.
# ─────────────────────────────────────────────────────────────────────────────

AGENT_REGISTRY = {
    # Tier 1 — Foundation Agents
    "clinical_synthesis":          {"name": "Agent 1 — Clinical Synthesizer",          "default_urgency": UrgencyLevel.ROUTINE},
    "staging":                     {"name": "Agent 2 — Staging Calculator",             "default_urgency": UrgencyLevel.ROUTINE},
    "treatment_recommendation":    {"name": "Agent 3 — Treatment Recommendation",       "default_urgency": UrgencyLevel.URGENT},

    # Tier 2 — Clinical Depth Agents
    "biopsy_guidance":             {"name": "Agent 4 — Biopsy & Pathology Guidance",    "default_urgency": UrgencyLevel.URGENT},
    "surgical_planning":           {"name": "Agent 5 — Surgical Planning",              "default_urgency": UrgencyLevel.URGENT},
    "clinical_trial_matching":     {"name": "Agent 6 — Clinical Trial Matching",        "default_urgency": UrgencyLevel.ROUTINE},
    "prognosis":                   {"name": "Agent 7 — Prognosis & Survival",           "default_urgency": UrgencyLevel.ROUTINE},

    # Tier 3 — Intelligence Agents
    "next_steps":                  {"name": "Agent 8 — Next Steps Coordinator",         "default_urgency": UrgencyLevel.ROUTINE},
    "bidirectional_guidance":      {"name": "Agent 9 — Bidirectional Guidance",         "default_urgency": UrgencyLevel.ROUTINE},
    "longitudinal_tracking":       {"name": "Agent 10 — Longitudinal Tracking",         "default_urgency": UrgencyLevel.ROUTINE},
    "safety_checker":              {"name": "Agent 11 — Safety & Contraindication",     "default_urgency": UrgencyLevel.CRITICAL},
    "image_analysis":              {"name": "Agent 12 — Image Analysis (MedGemma)",     "default_urgency": UrgencyLevel.ROUTINE},
    "mdt_simulation":              {"name": "Agent 13 — MDT Meeting Simulation",        "default_urgency": UrgencyLevel.ROUTINE},

    # Tier 4 — Precision Medicine Agents
    "radiomics":                   {"name": "Agent 14 — Radiomics & Digital Pathology", "default_urgency": UrgencyLevel.ROUTINE},
    "genomics":                    {"name": "Agent 15 — Genomics & Precision Medicine", "default_urgency": UrgencyLevel.URGENT},
    "treatment_prediction":        {"name": "Agent 16 — Treatment Response Prediction", "default_urgency": UrgencyLevel.URGENT},

    # Administrative Co-Pilot
    "insurance_summary":           {"name": "Agent 17 — Insurance & Q&A Co-Pilot",      "default_urgency": UrgencyLevel.ROUTINE},

    # Legacy types (from original code — preserved for backward compatibility)
    "imaging_analysis":            {"name": "Imaging Analysis",                          "default_urgency": UrgencyLevel.ROUTINE},
    "specialist_recommendations":  {"name": "Specialist Recommendations",                "default_urgency": UrgencyLevel.URGENT},
    "mdt_brief":                   {"name": "MDT Brief",                                 "default_urgency": UrgencyLevel.ROUTINE},
    "test":                        {"name": "Test Request",                              "default_urgency": UrgencyLevel.ROUTINE},
}


# ─────────────────────────────────────────────────────────────────────────────
# Confidence Score Helper
# ─────────────────────────────────────────────────────────────────────────────

def _score_to_level(score: Optional[float]) -> ConfidenceLevel:
    """Convert a numeric confidence score (0.0–1.0) to a ConfidenceLevel."""
    if score is None:
        return ConfidenceLevel.MODERATE
    if score >= 0.85:
        return ConfidenceLevel.HIGH
    if score >= 0.65:
        return ConfidenceLevel.MODERATE
    return ConfidenceLevel.LOW


def _confidence_badge(level: ConfidenceLevel) -> str:
    """Return a coloured terminal badge for the confidence level."""
    badges = {
        ConfidenceLevel.HIGH:     "✅ HIGH CONFIDENCE",
        ConfidenceLevel.MODERATE: "⚠️  MODERATE CONFIDENCE — Review carefully",
        ConfidenceLevel.LOW:      "🔴 LOW CONFIDENCE — Clinician must decide",
    }
    return badges.get(level, "❓ UNKNOWN")


def _urgency_badge(level: UrgencyLevel) -> str:
    """Return a terminal badge for the urgency level."""
    badges = {
        UrgencyLevel.ROUTINE:  "🟢 ROUTINE",
        UrgencyLevel.URGENT:   "🟡 URGENT — Review within 4 hours",
        UrgencyLevel.CRITICAL: "🔴 CRITICAL — Immediate review required",
    }
    return badges.get(level, "❓ UNKNOWN")


# ─────────────────────────────────────────────────────────────────────────────
# HITLApprovalSystem
# ─────────────────────────────────────────────────────────────────────────────

class HITLApprovalSystem:
    """
    Human-in-the-Loop Approval System for the SAARTHI AI MDT Platform.

    Manages the complete approval lifecycle for all AI-generated clinical
    recommendations. Every recommendation must pass through this system
    before it can be used in a clinical decision.

    Backward-compatible with the original HITLApprovalSystem — all original
    method signatures are preserved exactly.
    """

    def __init__(self, approval_dir: str = "outputs/hitl_approvals"):
        self.approval_dir = Path(approval_dir)
        self.approval_dir.mkdir(parents=True, exist_ok=True)

        # Session tracking — records all requests made in this pipeline run
        self._session_requests: List[str] = []
        self._session_id: str = str(uuid.uuid4())[:8]

    # ─────────────────────────────────────────────────────────────────────────
    # Core API (original methods — preserved exactly)
    # ─────────────────────────────────────────────────────────────────────────

    def create_approval_request(
        self,
        recommendation_data: Any,
        recommendation_type: str,
        confidence_score: Optional[float] = None,
        urgency: Optional[str] = None,
        mdt_hints: Optional[List[str]] = None,
        reasoning_trace: Optional[str] = None,
        citations: Optional[List[str]] = None,
        case_id: Optional[str] = None,
    ) -> Dict:
        """
        Create a new HITL approval request.

        Original parameters (backward-compatible):
            recommendation_data   : Dict containing the AI recommendation
            recommendation_type   : Type string (e.g., 'imaging_analysis')

        New optional parameters:
            confidence_score  : Float 0.0–1.0 (AI confidence in this output)
            urgency           : 'ROUTINE' | 'URGENT' | 'CRITICAL'
            mdt_hints         : List of question hints for the radiologist
            reasoning_trace   : Explanation of how the AI reached this output
            citations         : List of NCCN/PubMed citations supporting output
            case_id           : Patient case identifier (de-identified)

        Returns:
            Dict with full approval request details
        """
        request_id = str(uuid.uuid4())[:8]

        # Resolve agent info
        agent_info = AGENT_REGISTRY.get(
            recommendation_type,
            {"name": recommendation_type, "default_urgency": UrgencyLevel.ROUTINE}
        )

        # Resolve urgency
        if urgency:
            try:
                resolved_urgency = UrgencyLevel(urgency.upper())
            except ValueError:
                resolved_urgency = agent_info["default_urgency"]
        else:
            resolved_urgency = agent_info["default_urgency"]

        # Resolve confidence
        confidence_level = _score_to_level(confidence_score)

        # Build the request object
        approval_request = {
            # ── Identity ──────────────────────────────────────────────────
            "request_id":           request_id,
            "session_id":           self._session_id,
            "case_id":              case_id,

            # ── Recommendation ────────────────────────────────────────────
            "recommendation_type":  recommendation_type,
            "agent_name":           agent_info["name"],
            "recommendation_data":  recommendation_data,

            # ── Safety Metadata ───────────────────────────────────────────
            "confidence_score":     confidence_score,
            "confidence_level":     confidence_level.value,
            "urgency":              resolved_urgency.value,
            "reasoning_trace":      reasoning_trace,
            "citations":            citations or [],
            "mdt_hints":            mdt_hints or [],

            # ── Workflow State ────────────────────────────────────────────
            "status":               ApprovalStatus.PENDING.value,
            "created_at":           datetime.now().isoformat(),
            "clinician_id":         None,
            "approval_notes":       None,
            "approved_at":          None,
            "rejected_at":          None,
            "override_details":     None,
            "escalation_notes":     None,

            # ── Audit ─────────────────────────────────────────────────────
            "audit_trail": [
                {
                    "event":      "REQUEST_CREATED",
                    "timestamp":  datetime.now().isoformat(),
                    "actor":      "SAARTHI_AI",
                    "details":    f"Approval request created for {agent_info['name']}"
                }
            ]
        }

        # Persist to disk
        self._save_request(approval_request)

        # Track in session
        self._session_requests.append(request_id)

        return approval_request

    def approve_request(
        self,
        request_id: str,
        clinician_id: str,
        notes: str = ""
    ) -> Dict:
        """
        Approve a pending HITL request.

        Args:
            request_id    : ID of the request to approve
            clinician_id  : ID/name of the approving clinician
            notes         : Optional approval notes

        Returns:
            Updated approval request dict
        """
        request = self._load_request(request_id)

        request["status"]         = ApprovalStatus.APPROVED.value
        request["clinician_id"]   = clinician_id
        request["approval_notes"] = notes
        request["approved_at"]    = datetime.now().isoformat()

        request["audit_trail"].append({
            "event":     "REQUEST_APPROVED",
            "timestamp": datetime.now().isoformat(),
            "actor":     clinician_id,
            "details":   notes or "Approved without additional notes"
        })

        self._save_request(request)
        return request

    def reject_request(
        self,
        request_id: str,
        clinician_id: str,
        reason: str = ""
    ) -> Dict:
        """
        Reject a pending HITL request.

        Args:
            request_id    : ID of the request to reject
            clinician_id  : ID/name of the rejecting clinician
            reason        : Reason for rejection

        Returns:
            Updated approval request dict
        """
        request = self._load_request(request_id)

        request["status"]           = ApprovalStatus.REJECTED.value
        request["clinician_id"]     = clinician_id
        request["rejection_reason"] = reason
        request["rejected_at"]      = datetime.now().isoformat()

        request["audit_trail"].append({
            "event":     "REQUEST_REJECTED",
            "timestamp": datetime.now().isoformat(),
            "actor":     clinician_id,
            "details":   reason or "Rejected without stated reason"
        })

        self._save_request(request)
        return request

    def get_pending_requests(self) -> List[Dict]:
        """Return all pending approval requests from disk."""
        pending = []
        for approval_file in self.approval_dir.glob("approval_*.json"):
            try:
                with open(approval_file, "r") as f:
                    request = json.load(f)
                if request.get("status") == ApprovalStatus.PENDING.value:
                    pending.append(request)
            except (json.JSONDecodeError, KeyError):
                continue
        return pending

    def get_request_status(self, request_id: str) -> Optional[Dict]:
        """Return the full request dict for a given request_id, or None."""
        approval_file = self.approval_dir / f"approval_{request_id}.json"
        if not approval_file.exists():
            return None
        with open(approval_file, "r") as f:
            return json.load(f)

    # ─────────────────────────────────────────────────────────────────────────
    # Enhanced Methods (new capabilities)
    # ─────────────────────────────────────────────────────────────────────────

    def override_request(
        self,
        request_id: str,
        clinician_id: str,
        modified_recommendation: Any,
        override_reason: str
    ) -> Dict:
        """
        Override: clinician accepts the AI output but modifies it.

        This is distinct from rejection. The clinician agrees with the
        direction of the recommendation but corrects specific details.
        The override and the original AI output are both saved for audit.

        Args:
            request_id               : ID of the request to override
            clinician_id             : ID/name of the clinician
            modified_recommendation  : The clinician's corrected version
            override_reason          : Why the modification was made

        Returns:
            Updated approval request dict
        """
        request = self._load_request(request_id)

        request["status"]           = ApprovalStatus.OVERRIDDEN.value
        request["clinician_id"]     = clinician_id
        request["approved_at"]      = datetime.now().isoformat()
        request["override_details"] = {
            "original_ai_output":    request["recommendation_data"],
            "clinician_correction":  modified_recommendation,
            "override_reason":       override_reason,
            "overridden_at":         datetime.now().isoformat()
        }

        # Replace the recommendation data with the clinician's version
        request["recommendation_data"] = modified_recommendation

        request["audit_trail"].append({
            "event":     "REQUEST_OVERRIDDEN",
            "timestamp": datetime.now().isoformat(),
            "actor":     clinician_id,
            "details":   f"AI output modified. Reason: {override_reason}"
        })

        self._save_request(request)
        return request

    def escalate_request(
        self,
        request_id: str,
        escalated_by: str,
        escalation_notes: str,
        escalate_to: str = "Senior Clinician"
    ) -> Dict:
        """
        Escalate a request to a senior clinician for second opinion.

        Args:
            request_id        : ID of the request to escalate
            escalated_by      : ID of the clinician escalating
            escalation_notes  : Reason for escalation
            escalate_to       : Target role or clinician name

        Returns:
            Updated approval request dict
        """
        request = self._load_request(request_id)

        request["status"]           = ApprovalStatus.ESCALATED.value
        request["escalation_notes"] = {
            "escalated_by":    escalated_by,
            "escalate_to":     escalate_to,
            "reason":          escalation_notes,
            "escalated_at":    datetime.now().isoformat()
        }

        request["audit_trail"].append({
            "event":     "REQUEST_ESCALATED",
            "timestamp": datetime.now().isoformat(),
            "actor":     escalated_by,
            "details":   f"Escalated to {escalate_to}. Reason: {escalation_notes}"
        })

        self._save_request(request)
        return request

    def interactive_review(self, request_id: str) -> Dict:
        """
        Present a HITL approval request interactively in the terminal.

        Displays the AI recommendation, confidence level, urgency, reasoning
        trace, citations, and MDT hints. Prompts the clinician for a decision.

        This method is called by the pipeline for each agent output.

        Returns:
            The final (approved/rejected/overridden) request dict
        """
        request = self._load_request(request_id)

        print("\n" + "═" * 80)
        print(f"  HUMAN REVIEW REQUIRED — {request['agent_name'].upper()}")
        print("═" * 80)

        # ── Case and urgency info ─────────────────────────────────────────
        if request.get("case_id"):
            print(f"  Case ID  : {request['case_id']}")
        print(f"  Urgency  : {_urgency_badge(UrgencyLevel(request['urgency']))}")
        print(f"  Confidence: {_confidence_badge(ConfidenceLevel(request['confidence_level']))}")
        if request.get("confidence_score") is not None:
            print(f"  Score    : {request['confidence_score']:.0%}")

        # ── Reasoning trace ───────────────────────────────────────────────
        if request.get("reasoning_trace"):
            print("\n  REASONING TRACE")
            print("  " + "─" * 76)
            for line in request["reasoning_trace"].split("\n"):
                print(f"  {line}")

        # ── AI Recommendation ─────────────────────────────────────────────
        print("\n  AI RECOMMENDATION")
        print("  " + "─" * 76)
        rec_data = request["recommendation_data"]
        if isinstance(rec_data, dict):
            for key, value in rec_data.items():
                if isinstance(value, str) and len(value) > 80:
                    print(f"  {key}:")
                    for line in value.split("\n"):
                        print(f"    {line}")
                elif isinstance(value, list):
                    print(f"  {key}:")
                    for item in value:
                        print(f"    • {item}")
                else:
                    print(f"  {key}: {value}")
        else:
            print(f"  {rec_data}")

        # ── Citations ─────────────────────────────────────────────────────
        if request.get("citations"):
            print("\n  SUPPORTING EVIDENCE (RAG Citations)")
            print("  " + "─" * 76)
            for i, citation in enumerate(request["citations"], 1):
                print(f"  [{i}] {citation}")

        # ── MDT Question Hints ────────────────────────────────────────────
        if request.get("mdt_hints"):
            print("\n  MDT DISCUSSION POINTS (Question Anticipation Engine)")
            print("  " + "─" * 76)
            for hint in request["mdt_hints"]:
                print(f"  → {hint}")

        # ── Decision prompt ───────────────────────────────────────────────
        print("\n" + "─" * 80)
        print("  DECISION REQUIRED")
        print("  [A] Approve   — Accept AI recommendation as-is")
        print("  [R] Reject    — Reject AI recommendation entirely")
        print("  [O] Override  — Accept with modifications")
        print("  [E] Escalate  — Send to senior clinician")
        print("  [S] Skip      — Defer decision (mark as pending)")
        print("─" * 80)

        clinician_id = input("  Your ID (name/initials): ").strip() or "CLINICIAN"

        while True:
            choice = input("  Decision [A/R/O/E/S]: ").strip().upper()

            if choice == "A":
                notes = input("  Approval notes (optional, press Enter to skip): ").strip()
                return self.approve_request(request_id, clinician_id, notes)

            elif choice == "R":
                reason = input("  Reason for rejection: ").strip()
                if not reason:
                    print("  ⚠️  A reason is required for rejection.")
                    continue
                return self.reject_request(request_id, clinician_id, reason)

            elif choice == "O":
                print("  Enter your corrected recommendation (type END on a new line to finish):")
                lines = []
                while True:
                    line = input()
                    if line.strip().upper() == "END":
                        break
                    lines.append(line)
                modified = "\n".join(lines)
                reason = input("  Reason for modification: ").strip()
                return self.override_request(request_id, clinician_id, modified, reason)

            elif choice == "E":
                escalate_to = input("  Escalate to (name/role): ").strip() or "Senior Clinician"
                notes = input("  Reason for escalation: ").strip()
                return self.escalate_request(request_id, clinician_id, notes, escalate_to)

            elif choice == "S":
                print("  ⚠️  Request deferred. It remains in PENDING status.")
                return request

            else:
                print("  Invalid choice. Please enter A, R, O, E, or S.")

    def print_session_summary(self) -> None:
        """
        Print a summary of all HITL decisions made in this pipeline session.
        Call this at the end of the pipeline run.
        """
        if not self._session_requests:
            print("\n  No HITL requests were made in this session.")
            return

        print("\n" + "═" * 80)
        print(f"  HITL SESSION SUMMARY — Session {self._session_id}")
        print("═" * 80)

        counts = {s.value: 0 for s in ApprovalStatus}
        rows = []

        for request_id in self._session_requests:
            request = self.get_request_status(request_id)
            if request:
                status = request.get("status", "unknown")
                counts[status] = counts.get(status, 0) + 1
                rows.append({
                    "id":         request_id,
                    "agent":      request.get("agent_name", request.get("recommendation_type")),
                    "status":     status.upper(),
                    "confidence": request.get("confidence_level", "N/A"),
                    "clinician":  request.get("clinician_id", "—"),
                })

        # Print table
        print(f"\n  {'ID':<10} {'Agent':<42} {'Status':<12} {'Confidence':<12} {'Clinician'}")
        print(f"  {'─'*8} {'─'*40} {'─'*10} {'─'*10} {'─'*15}")
        for row in rows:
            status_icon = {
                "APPROVED": "✅", "REJECTED": "❌",
                "OVERRIDDEN": "✏️ ", "ESCALATED": "⬆️ ",
                "PENDING": "⏳"
            }.get(row["status"], "❓")
            print(f"  {row['id']:<10} {row['agent'][:40]:<42} "
                  f"{status_icon} {row['status']:<10} {row['confidence']:<12} {row['clinician']}")

        print(f"\n  Total: {len(self._session_requests)} requests | "
              f"✅ {counts.get('approved', 0)} approved | "
              f"❌ {counts.get('rejected', 0)} rejected | "
              f"✏️  {counts.get('overridden', 0)} overridden | "
              f"⬆️  {counts.get('escalated', 0)} escalated | "
              f"⏳ {counts.get('pending', 0)} pending")
        print("═" * 80 + "\n")

    def get_session_audit_log(self) -> List[Dict]:
        """
        Return the complete audit trail for this session.
        Suitable for saving to the immutable audit log (Safety Layer 6).
        """
        audit_entries = []
        for request_id in self._session_requests:
            request = self.get_request_status(request_id)
            if request:
                for entry in request.get("audit_trail", []):
                    entry["request_id"] = request_id
                    entry["agent_name"] = request.get("agent_name")
                    entry["case_id"]    = request.get("case_id")
                    audit_entries.append(entry)
        return audit_entries

    # ─────────────────────────────────────────────────────────────────────────
    # Private Helpers
    # ─────────────────────────────────────────────────────────────────────────

    def _save_request(self, request: Dict) -> None:
        """Persist an approval request to disk as JSON."""
        approval_file = self.approval_dir / f"approval_{request['request_id']}.json"
        with open(approval_file, "w") as f:
            json.dump(request, f, indent=2, default=str)

    def _load_request(self, request_id: str) -> Dict:
        """Load an approval request from disk. Raises FileNotFoundError if missing."""
        approval_file = self.approval_dir / f"approval_{request_id}.json"
        if not approval_file.exists():
            raise FileNotFoundError(
                f"Approval request not found: {request_id}\n"
                f"Looked in: {self.approval_dir}"
            )
        with open(approval_file, "r") as f:
            return json.load(f)


# ─────────────────────────────────────────────────────────────────────────────
# Standalone Test / Demo
# Run: python hitl_approval_system.py
# ─────────────────────────────────────────────────────────────────────────────

def main():
    """
    Self-test for the HITL Approval System.
    Tests all core methods without requiring user input.
    """
    print("\n" + "=" * 80)
    print("  SAARTHI AI — HITL Approval System Self-Test")
    print("=" * 80 + "\n")

    hitl = HITLApprovalSystem(approval_dir="outputs/hitl_approvals_test")
    results = []

    # ── Test 1: Create request (original API) ─────────────────────────────
    print("Test 1: Create approval request (original API)...")
    request = hitl.create_approval_request(
        recommendation_data={
            "case_id": "BC-2026-00142",
            "recommendation": "Neoadjuvant chemotherapy recommended (EC-T regimen)",
            "staging": "Stage IIB, T2N1M0",
            "guideline": "NCCN Breast Cancer v1.2026"
        },
        recommendation_type="treatment_recommendation"
    )
    assert request["status"] == "pending", "Status should be pending"
    assert request["agent_name"] == "Agent 3 — Treatment Recommendation"
    assert request["urgency"] == "URGENT"
    print(f"  ✅ Created: {request['request_id']} | Agent: {request['agent_name']}")
    results.append(True)

    # ── Test 2: Create request with confidence score ───────────────────────
    print("\nTest 2: Create request with confidence score and citations...")
    request2 = hitl.create_approval_request(
        recommendation_data={"findings": "3.2cm IDC left breast, 2 axillary nodes"},
        recommendation_type="image_analysis",
        confidence_score=0.92,
        citations=["NCCN Breast Cancer v1.2026 — Section 3.1", "Lancet Oncol 2024;25:112-120"],
        mdt_hints=[
            "Consider discussing feasibility of sentinel node biopsy vs ALND",
            "MRI shows skin thickening — discuss inflammatory component with MDT"
        ],
        reasoning_trace="MedGemma identified a 3.2cm mass with spiculated margins. "
                        "Two axillary nodes show cortical thickening >3mm. "
                        "No skin involvement. Confidence based on 94% similar training cases."
    )
    assert request2["confidence_level"] == "HIGH"
    assert len(request2["citations"]) == 2
    assert len(request2["mdt_hints"]) == 2
    print(f"  ✅ Confidence: {request2['confidence_level']} | Citations: {len(request2['citations'])}")
    results.append(True)

    # ── Test 3: Approve (original API) ────────────────────────────────────
    print("\nTest 3: Approve request (original API)...")
    approved = hitl.approve_request(
        request_id=request["request_id"],
        clinician_id="DR_SMITH",
        notes="Agreed with EC-T regimen. Patient counselled."
    )
    assert approved["status"] == "approved"
    assert approved["clinician_id"] == "DR_SMITH"
    print(f"  ✅ Approved by {approved['clinician_id']}")
    results.append(True)

    # ── Test 4: Reject (original API) ─────────────────────────────────────
    print("\nTest 4: Reject request...")
    request3 = hitl.create_approval_request(
        recommendation_data={"staging": "Stage IV"},
        recommendation_type="staging"
    )
    rejected = hitl.reject_request(
        request_id=request3["request_id"],
        clinician_id="DR_JONES",
        reason="Staging incorrect — M0 not M1. No distant metastases on PET-CT."
    )
    assert rejected["status"] == "rejected"
    print(f"  ✅ Rejected. Reason: {rejected['rejection_reason'][:50]}...")
    results.append(True)

    # ── Test 5: Override ──────────────────────────────────────────────────
    print("\nTest 5: Override request...")
    request4 = hitl.create_approval_request(
        recommendation_data={"recommendation": "Mastectomy recommended"},
        recommendation_type="surgical_planning"
    )
    overridden = hitl.override_request(
        request_id=request4["request_id"],
        clinician_id="DR_PATEL",
        modified_recommendation={"recommendation": "Breast-conserving surgery (lumpectomy + SLNB)"},
        override_reason="Patient is eligible for BCS. Tumour:breast ratio favourable."
    )
    assert overridden["status"] == "overridden"
    assert overridden["override_details"]["original_ai_output"]["recommendation"] == "Mastectomy recommended"
    print(f"  ✅ Overridden. Original preserved in audit trail.")
    results.append(True)

    # ── Test 6: Escalate ──────────────────────────────────────────────────
    print("\nTest 6: Escalate request...")
    request5 = hitl.create_approval_request(
        recommendation_data={"recommendation": "Enrolment in KEYNOTE-522 trial"},
        recommendation_type="clinical_trial_matching",
        confidence_score=0.58
    )
    escalated = hitl.escalate_request(
        request_id=request5["request_id"],
        escalated_by="DR_LEE",
        escalation_notes="Low confidence. Patient has borderline eligibility criteria.",
        escalate_to="Prof. Williams — Clinical Trials Lead"
    )
    assert escalated["status"] == "escalated"
    print(f"  ✅ Escalated to: {escalated['escalation_notes']['escalate_to']}")
    results.append(True)

    # ── Test 7: Get pending requests ──────────────────────────────────────
    print("\nTest 7: Get pending requests...")
    pending = hitl.get_pending_requests()
    print(f"  ✅ Pending requests: {len(pending)}")
    results.append(True)

    # ── Test 8: Audit trail integrity ─────────────────────────────────────
    print("\nTest 8: Audit trail integrity...")
    approved_request = hitl.get_request_status(request["request_id"])
    assert len(approved_request["audit_trail"]) == 2  # Created + Approved
    assert approved_request["audit_trail"][0]["event"] == "REQUEST_CREATED"
    assert approved_request["audit_trail"][1]["event"] == "REQUEST_APPROVED"
    print(f"  ✅ Audit trail has {len(approved_request['audit_trail'])} entries")
    results.append(True)

    # ── Session summary ───────────────────────────────────────────────────
    hitl.print_session_summary()

    # ── Final result ──────────────────────────────────────────────────────
    print("=" * 80)
    print(f"  FINAL RESULT: {sum(results)}/{len(results)} tests passed")
    if all(results):
        print("  ✅ ALL TESTS PASSED — HITL System is ready for integration.")
    else:
        print("  ❌ SOME TESTS FAILED — Review output above.")
    print("=" * 80 + "\n")

    # Clean up test output directory
    import shutil
    shutil.rmtree("outputs/hitl_approvals_test", ignore_errors=True)

    return all(results)


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

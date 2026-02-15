"""
Human-in-the-Loop (HITL) Approval System
Manages approval workflow for AI-generated recommendations
"""

import json
from pathlib import Path
from datetime import datetime
import uuid

class HITLApprovalSystem:
    def __init__(self):
        self.approval_dir = Path("outputs/hitl_approvals")
        self.approval_dir.mkdir(parents=True, exist_ok=True)
    
    def create_approval_request(self, recommendation_data, recommendation_type):
        """
        Create a new approval request
        
        Args:
            recommendation_data: Dict containing the recommendation
            recommendation_type: Type of recommendation (e.g., 'imaging_analysis', 'specialist_recommendations')
        
        Returns:
            Dict with approval request details
        """
        
        request_id = str(uuid.uuid4())[:8]
        
        approval_request = {
            "request_id": request_id,
            "recommendation_type": recommendation_type,
            "recommendation_data": recommendation_data,
            "status": "pending",
            "created_at": datetime.now().isoformat(),
            "clinician_id": None,
            "approval_notes": None,
            "approved_at": None
        }
        
        # Save approval request
        approval_file = self.approval_dir / f"approval_{request_id}.json"
        with open(approval_file, 'w') as f:
            json.dump(approval_request, f, indent=2)
        
        return approval_request
    
    def approve_request(self, request_id, clinician_id, notes=""):
        """
        Approve a pending HITL request
        
        Args:
            request_id: ID of the request to approve
            clinician_id: ID of the clinician approving
            notes: Optional approval notes
        
        Returns:
            Updated approval request
        """
        
        approval_file = self.approval_dir / f"approval_{request_id}.json"
        
        if not approval_file.exists():
            raise FileNotFoundError(f"Approval request not found: {request_id}")
        
        # Load existing request
        with open(approval_file, 'r') as f:
            approval_request = json.load(f)
        
        # Update status
        approval_request["status"] = "approved"
        approval_request["clinician_id"] = clinician_id
        approval_request["approval_notes"] = notes
        approval_request["approved_at"] = datetime.now().isoformat()
        
        # Save updated request
        with open(approval_file, 'w') as f:
            json.dump(approval_request, f, indent=2)
        
        return approval_request
    
    def reject_request(self, request_id, clinician_id, reason=""):
        """
        Reject a pending HITL request
        
        Args:
            request_id: ID of the request to reject
            clinician_id: ID of the clinician rejecting
            reason: Reason for rejection
        
        Returns:
            Updated approval request
        """
        
        approval_file = self.approval_dir / f"approval_{request_id}.json"
        
        if not approval_file.exists():
            raise FileNotFoundError(f"Approval request not found: {request_id}")
        
        # Load existing request
        with open(approval_file, 'r') as f:
            approval_request = json.load(f)
        
        # Update status
        approval_request["status"] = "rejected"
        approval_request["clinician_id"] = clinician_id
        approval_request["rejection_reason"] = reason
        approval_request["rejected_at"] = datetime.now().isoformat()
        
        # Save updated request
        with open(approval_file, 'w') as f:
            json.dump(approval_request, f, indent=2)
        
        return approval_request
    
    def get_pending_requests(self):
        """Get all pending approval requests"""
        
        pending = []
        for approval_file in self.approval_dir.glob("approval_*.json"):
            with open(approval_file, 'r') as f:
                request = json.load(f)
                if request["status"] == "pending":
                    pending.append(request)
        
        return pending
    
    def get_request_status(self, request_id):
        """Get status of a specific request"""
        
        approval_file = self.approval_dir / f"approval_{request_id}.json"
        
        if not approval_file.exists():
            return None
        
        with open(approval_file, 'r') as f:
            return json.load(f)


def main():
    """Test HITL approval system"""
    
    print("\n" + "="*80)
    print("TESTING HITL APPROVAL SYSTEM")
    print("="*80 + "\n")
    
    hitl = HITLApprovalSystem()
    
    # Create test approval request
    print("Creating approval request...")
    request = hitl.create_approval_request(
        recommendation_data={
            "case_id": "TEST-001",
            "recommendation": "Test recommendation"
        },
        recommendation_type="test"
    )
    
    print(f"✅ Request created: {request['request_id']}")
    print(f"   Status: {request['status']}")
    
    # Approve request
    print("\nApproving request...")
    approved = hitl.approve_request(
        request_id=request['request_id'],
        clinician_id="DR_TEST",
        notes="Test approval"
    )
    
    print(f"✅ Request approved: {approved['request_id']}")
    print(f"   Status: {approved['status']}")
    print(f"   Clinician: {approved['clinician_id']}")
    
    print("\n" + "="*80)
    print("HITL SYSTEM TEST COMPLETE")
    print("="*80 + "\n")


if __name__ == "__main__":
    main()

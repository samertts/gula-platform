#!/usr/bin/env python3
"""
GULA Advanced Contextual RBAC & Secure Assistant Middleware (Enhanced)
-----------------------------------------------------------------
Description: Implements Role-Based Access Control (RBAC) combined with Contextual 
Departmental Authorization (ABAC) to restrict access based on hospital departments.
"""

import logging
from typing import Dict, Any, List

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] GULA-CONTEXT-RBAC: %(message)s'
)

class ContextualRBACManager:
    def __init__(self):
        self.role_permissions = {
            "PHYSICIAN": ["read_phi", "write_clinical", "view_audit", "query_assistant_full"],
            "NURSE": ["read_phi", "write_vitals", "query_assistant_standard"],
            "TECHNICIAN": ["read_device_telemetry", "manage_gateways", "query_assistant_technical"],
            "ADMIN": ["read_phi", "read_device_telemetry", "manage_users", "view_audit", "system_config", "query_assistant_full"]
        }

    def authorize_with_context(self, user_role: str, user_department: str, target_department: str, required_permission: str) -> bool:
        """
        Verifies both role permissions and departmental context (ABAC) to prevent 
        cross-departmental data snooping (e.g., Cardiology physician accessing Psychiatry records).
        """
        user_role = user_role.upper()
        
        # 1. Role Permission Check
        if user_role not in self.role_permissions:
            logging.error(f"SECURITY VIOLATION: Unknown role '{user_role}'.")
            return False
            
        if required_permission not in self.role_permissions[user_role]:
            logging.warning(f"ACCESS DENIED: Role '{user_role}' lacks permission '{required_permission}'.")
            return False

        # 2. Contextual Departmental Check (Admin can access all, others require matching department or emergency override)
        if user_role != "ADMIN" and user_department != "GENERAL" and user_department != target_department:
            logging.warning(f"CONTEXTUAL ACCESS DENIED: User from department '{user_department}' attempted access to '{target_department}' records.")
            return False

        logging.info(f"CONTEXTUAL ACCESS GRANTED: Role '{user_role}' in dept '{user_department}' authorized for '{required_permission}'.")
        return True

class SecureAssistantWrapper:
    def __init__(self):
        self.rbac = ContextualRBACManager()

    def query_assistant(self, user_role: str, user_dept: str, target_dept: str, query_type: str) -> Dict[str, Any]:
        permission_map = {
            "clinical": "read_phi",
            "technical": "read_device_telemetry",
            "admin": "system_config"
        }
        required_perm = permission_map.get(query_type, "read_phi")
        
        if not self.rbac.authorize_with_context(user_role, user_dept, target_dept, required_perm):
            return {
                "status": "FORBIDDEN",
                "error": "Access denied. Insufficient role permissions or departmental context mismatch."
            }

        return {
            "status": "SUCCESS",
            "role": user_role,
            "department": user_dept,
            "data": f"Context-secured response delivered for query type '{query_type}' in department '{target_dept}'."
        }

if __name__ == "__main__":
    wrapper = SecureAssistantWrapper()
    
    # Test 1: Cardiology Physician querying Cardiology patient (Should succeed)
    print(wrapper.query_assistant("PHYSICIAN", "CARDIOLOGY", "CARDIOLOGY", "clinical"))

    # Test 2: Cardiology Physician attempting to query Psychiatry patient (Should fail due to departmental context)
    print(wrapper.query_assistant("PHYSICIAN", "CARDIOLOGY", "PSYCHIATRY", "clinical"))

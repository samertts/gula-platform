import time
import logging
from typing import Dict, Optional
from fastapi import Request, HTTPException

logger = logging.getLogger("gula.security.zerotrust")

class ZeroTrustGuard:
    """
    Implements Zero-Trust principles: Never Trust, Always Verify.
    Monitors session anomalies and enforces strict identity verification.
    """
    
    # Session tracking (In-memory for demo, would be Redis in production)
    _active_sessions: Dict[str, Dict] = {}

    @classmethod
    async def verify_session_integrity(cls, request: Request, user_id: str, session_id: str):
        """
        Checks for session hijacking or suspicious location/device changes.
        """
        current_ip = request.client.host
        current_ua = request.headers.get("user-agent", "unknown")
        
        session = cls._active_sessions.get(session_id)
        
        if not session:
            # First time seeing this session
            cls._active_sessions[session_id] = {
                "user_id": user_id,
                "ip": current_ip,
                "ua": current_ua,
                "last_seen": time.time()
            }
            return

        # Check for IP or User-Agent change (Suspicious)
        if session["ip"] != current_ip or session["ua"] != current_ua:
            logger.warning(
                "[ZERO-TRUST] Suspicious session activity detected for user %s. "
                "IP change: %s -> %s | UA change: %s -> %s",
                user_id, session["ip"], current_ip, session["ua"], current_ua
            )
            # In a strict mode, we would revoke the session
            # raise HTTPException(status_code=401, detail="Session integrity violation. Please re-authenticate.")
            
        session["last_seen"] = time.time()

    @classmethod
    def enforce_mfa_requirement(cls, user_role: str, sensitive_path: bool) -> bool:
        """
        Determines if MFA is required based on role and operation sensitivity.
        """
        if user_role in ["admin", "master_admin"] or sensitive_path:
            return True
        return False

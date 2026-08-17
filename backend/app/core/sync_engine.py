import uuid
import time
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger("gula.sync_engine")

class SyncEvent:
    """Represents a single data mutation event with version tracking."""
    def __init__(self, entity_type: str, entity_id: str, action: str, data: Dict, version: int = 1):
        self.event_id = str(uuid.uuid4())
        self.entity_type = entity_type
        self.entity_id = entity_id
        self.action = action # 'CREATE', 'UPDATE', 'DELETE'
        self.data = data
        self.version = version
        self.timestamp = time.time()

class OfflineSyncEngine:
    """
    Handles robust data persistence and synchronization for Omni-Network operations.
    Ensures clinical data is captured offline, version-checked, and synced securely.
    """
    def __init__(self, node_id: str):
        self.node_id = node_id
        self.local_event_log: List[SyncEvent] = []
        self.synced_event_ids = set()

    def capture_event(self, entity_type: str, entity_id: str, action: str, data: Dict, version: int = 1):
        """Captures a new clinical action in the local log with versioning."""
        event = SyncEvent(entity_type, entity_id, action, data, version)
        self.local_event_log.append(event)
        logger.info(f"[SYNC] Event captured offline: {action} on {entity_type}:{entity_id} (v{version})")
        return event.event_id

    def get_pending_events(self) -> List[SyncEvent]:
        """Returns events that haven't been successfully synced yet."""
        return [e for e in self.local_event_log if e.event_id not in self.synced_event_ids]

    def mark_as_synced(self, event_ids: List[str]):
        """Marks events as successfully propagated to the network."""
        for eid in event_ids:
            self.synced_event_ids.add(eid)
        logger.info(f"[SYNC] Marked {len(event_ids)} events as synced.")

    def reconcile_incoming(self, incoming_events: List[Dict]) -> List[Dict]:
        """
        Reconciles incoming events from peers using Last-Writer-Wins (LWW) 
        and strict version comparison to prevent silent data overwrites.
        """
        logger.info(f"[SYNC] Reconciling {len(incoming_events)} events from peer with LWW & version check.")
        reconciliation_results = []
        
        for event_data in incoming_events:
            incoming_version = event_data.get("version", 1)
            incoming_id = event_data.get("entity_id")
            incoming_ts = event_data.get("timestamp", 0)
            
            # Check against local event log for conflicts
            conflict_found = False
            for local_event in self.local_event_log:
                if local_event.entity_id == incoming_id:
                    if incoming_version < local_event.version:
                        conflict_found = True
                        logger.warning(f"[SYNC CONFLICT] Rejected stale update for {incoming_id} (incoming v{incoming_version} < local v{local_event.version})")
                        reconciliation_results.append({
                            "entity_id": incoming_id,
                            "status": "REJECTED_STALE",
                            "reason": "Local version is newer or equal"
                        })
                        break
                    elif incoming_version == local_event.version and incoming_ts <= local_event.timestamp:
                        conflict_found = True
                        reconciliation_results.append({
                            "entity_id": incoming_id,
                            "status": "REJECTED_LWW",
                            "reason": "Last-Writer-Wins tie-breaker favored local event"
                        })
                        break
            
            if not conflict_found:
                logger.info(f"[SYNC] Accepted incoming event for entity {incoming_id} (v{incoming_version})")
                reconciliation_results.append({
                    "entity_id": incoming_id,
                    "status": "ACCEPTED"
                })
                
        return reconciliation_results

    def purge_old_synced_events(self, days: int = 30):
        """Removes synced events older than specified days to keep the system lean and efficient."""
        cutoff_time = time.time() - (days * 86400)
        initial_count = len(self.local_event_log)
        
        self.local_event_log = [
            e for e in self.local_event_log 
            if e.event_id not in self.synced_event_ids or e.timestamp > cutoff_time
        ]
        
        purged_count = initial_count - len(self.local_event_log)
        logger.info(f"[SYNC] Purged {purged_count} old synced events from local log.")
        return purged_count

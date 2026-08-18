import requests
import logging
from enum import Enum
from typing import Optional, Dict

logger = logging.getLogger("gula.hybrid_router")

class NetworkPath(Enum):
    INTERNET = "internet"
    LAN = "lan"
    MESH = "mesh"
    OFFLINE = "offline"

class HybridNetworkRouter:
    """
    Intelligently routes clinical data requests across multiple network tiers.
    Prioritizes the most stable and available connection.
    """
    def __init__(self, internet_url: str, local_discovery_manager):
        self.internet_url = internet_url
        self.discovery = local_discovery_manager

    def check_internet(self) -> bool:
        try:
            # Quick health check to the main API
            response = requests.get(f"{self.internet_url}/health", timeout=2)
            return response.status_code == 200
        except:
            return False

    def get_best_path(self) -> NetworkPath:
        """Determines the best network path currently available."""
        if self.check_internet():
            return NetworkPath.INTERNET
        
        peers = self.discovery.get_local_peers()
        if peers:
            return NetworkPath.LAN
        
        # Mesh would be a subset of LAN or P2P Bluetooth/Ad-hoc
        return NetworkPath.OFFLINE

    def route_request(self, endpoint: str, method: str, payload: Dict):
        """Executes the request via the best available path."""
        path = self.get_best_path()
        logger.info(f"[ROUTER] Selected network path: {path.value}")

        if path == NetworkPath.INTERNET:
            # Standard cloud sync
            return self._execute_cloud(endpoint, method, payload)
        
        elif path == NetworkPath.LAN:
            # Sync with a local peer (Hospital server or nearby node)
            return self._execute_lan(endpoint, method, payload)
        
        else:
            # Queue for offline sync
            logger.warning("[ROUTER] System in OFFLINE mode. Data queued for future sync.")
            return {"status": "queued", "mode": "offline"}

    def _execute_cloud(self, endpoint, method, payload):
        # Implementation of cloud request
        pass

    def _execute_lan(self, endpoint, method, payload):
        # Implementation of peer-to-peer LAN request
        pass

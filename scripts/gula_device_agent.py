import socket
import json
import logging
import time
import requests
from app.core.omni_network import OmniNetworkManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("gula.device_agent")

class GulaDeviceAgent:
    """
    Lightweight agent to bridge any computer, printer, or lab equipment to GULA.
    Acts as a local proxy that joins the Mesh/LAN network.
    """
    def __init__(self, device_id: str, device_type: str, port: int = 9000):
        self.device_id = device_id
        self.device_type = device_type
        self.port = port
        self.network_manager = OmniNetworkManager(device_id, port)

    def start(self):
        """Starts the agent and announces its presence on the network."""
        logger.info(f"[AGENT] Starting GULA Agent for {self.device_id} ({self.device_type})...")
        self.network_manager.advertise()
        self.network_manager.start_discovery()
        
        try:
            while True:
                # Monitor local peers and handle incoming bridge requests
                peers = self.network_manager.get_local_peers()
                if peers:
                    logger.debug(f"[AGENT] Active GULA peers found: {len(peers)}")
                time.sleep(10)
        except KeyboardInterrupt:
            self.stop()

    def send_data(self, target_node_ip: str, clinical_data: dict):
        """Sends captured data (e.g., from a scanner or analyzer) to a GULA node."""
        url = f"http://{target_node_ip}:8000/api/v1/ingest"
        try:
            response = requests.post(url, json=clinical_data, timeout=5)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"[AGENT] Failed to send data to {target_node_ip}: {e}")
            return False

    def stop(self):
        logger.info("[AGENT] Stopping GULA Agent...")
        self.network_manager.stop()

if __name__ == "__main__":
    # Example: Running as a Lab Analyzer Bridge
    agent = GulaDeviceAgent("LAB-ANALYZER-01", "Laboratory-Equipment")
    agent.start()

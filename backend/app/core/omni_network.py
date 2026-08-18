import socket
import logging
from zeroconf import ServiceInfo, Zeroconf, ServiceBrowser, ServiceListener

logger = logging.getLogger("gula.omni_network")

class GulaServiceListener(ServiceListener):
    def __init__(self):
        self.discovered_nodes = {}

    def update_service(self, zc: Zeroconf, type_: str, name: str) -> None:
        pass

    def remove_service(self, zc: Zeroconf, type_: str, name: str) -> None:
        if name in self.discovered_nodes:
            logger.info(f"[OMNI] Node offline: {name}")
            del self.discovered_nodes[name]

    def add_service(self, zc: Zeroconf, type_: str, name: str) -> None:
        info = zc.get_service_info(type_, name)
        if info:
            addresses = [socket.inet_ntoa(addr) for addr in info.addresses]
            self.discovered_nodes[name] = {
                "address": addresses[0] if addresses else None,
                "port": info.port,
                "properties": info.properties
            }
            logger.info(f"[OMNI] Discovered local GULA node: {name} at {addresses[0]}:{info.port}")

class OmniNetworkManager:
    """
    Manages GULA node presence and discovery on local networks (LAN).
    Enables communication without a central internet server.
    """
    SERVICE_TYPE = "_gula-clinical._tcp.local."

    def __init__(self, node_name: str, port: int):
        self.node_name = node_name
        self.port = port
        self.zeroconf = Zeroconf()
        self.listener = GulaServiceListener()
        self.browser = None

    def advertise(self):
        """Broadcasts this node's presence to the local network."""
        local_ip = socket.gethostbyname(socket.gethostname())
        info = ServiceInfo(
            self.SERVICE_TYPE,
            f"{self.node_name}.{self.SERVICE_TYPE}",
            addresses=[socket.inet_aton(local_ip)],
            port=self.port,
            properties={"version": "1.0", "type": "clinical-node"},
            server=f"{self.node_name}.local.",
        )
        logger.info(f"[OMNI] Advertising GULA node '{self.node_name}' on LAN at {local_ip}:{self.port}")
        self.zeroconf.register_service(info)

    def start_discovery(self):
        """Starts searching for other GULA nodes on the LAN."""
        logger.info("[OMNI] Starting local peer discovery...")
        self.browser = ServiceBrowser(self.zeroconf, self.SERVICE_TYPE, self.listener)

    def get_local_peers(self):
        return self.listener.discovered_nodes

    def stop(self):
        if self.browser:
            self.browser.cancel()
        self.zeroconf.unregister_all_services()
        self.zeroconf.close()

if __name__ == "__main__":
    # Test simulation
    logging.basicConfig(level=logging.INFO)
    manager = OmniNetworkManager("Hospital-Alpha-Unit", 8000)
    try:
        manager.advertise()
        manager.start_discovery()
        import time
        time.sleep(5)
        print("Discovered Peers:", manager.get_local_peers())
    finally:
        manager.stop()

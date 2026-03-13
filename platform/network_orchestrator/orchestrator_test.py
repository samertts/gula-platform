from lab_registry import register_lab
from orchestrator_engine import network_health, route_test_request

register_lab("Lab Alpha", "Baghdad", 120)
register_lab("Lab Beta", "Baghdad", 80)

print(network_health())

print(route_test_request("Baghdad"))

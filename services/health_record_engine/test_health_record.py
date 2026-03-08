from ai_health_alerts import health_alert
from record_manager import add_test_result
from record_reader import get_patient_history

nhid = "NH-123456"

add_test_result(nhid, "Glucose", "100")
add_test_result(nhid, "Glucose", "130")

print(get_patient_history(nhid))

print(health_alert(nhid, "Glucose"))

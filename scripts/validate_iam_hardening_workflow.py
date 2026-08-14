from pathlib import Path

import yaml

workflow = Path(".github/workflows/iam-hardening.yml")
data = yaml.safe_load(workflow.read_text())
assert isinstance(data, dict)
assert set(data["jobs"]) == {"backend-identity", "migration", "frontend-v3"}
triggers = data.get("on", data.get(True))
assert isinstance(triggers, dict)
assert "pull_request" in triggers
assert "push" in triggers
for job_name, job in data["jobs"].items():
    assert job["runs-on"] == "ubuntu-latest", job_name
    assert any(step.get("uses", "").startswith("actions/upload-artifact@") for step in job["steps"])
print("IAM hardening workflow structure is valid")

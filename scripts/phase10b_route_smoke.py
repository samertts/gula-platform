import os

os.environ.setdefault("ENV", "test")
os.environ.setdefault("BASE_URL", "http://localhost")
os.environ.setdefault("SECRET_KEY", "phase10b-local-smoke-secret")

from app.factory import create_app

app = create_app()
paths = {route.path for route in app.routes}
assert "/api/v1/clinical/patients" in paths
assert "/api/v1/clinical/orders" in paths
print("clinical_routes=mounted")

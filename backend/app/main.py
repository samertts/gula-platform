
from fastapi import FastAPI

from .routes import login
from .routes import identity
from .routes import labs
from .routes import results
from .routes import notifications
from .routes import dashboard

app=FastAPI(title="GULA Platform API")

app.include_router(login.router)
app.include_router(identity.router)
app.include_router(labs.router)
app.include_router(results.router)
app.include_router(notifications.router)
app.include_router(dashboard.router)

@app.get("/")

def root():

    return {"system":"GULA running"}

from .routes import register
from .routes import ehr
app.include_router(register.router)
app.include_router(ehr.router)
from .routes import security
app.include_router(security.router)
from .routes import national_identity
from .routes import insurance
from .routes import device_results
app.include_router(national_identity.router)
app.include_router(insurance.router)
app.include_router(device_results.router)

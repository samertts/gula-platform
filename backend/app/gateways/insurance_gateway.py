"""
Gateway placeholder for Iraqi Health Insurance system
Law No.22 of 2020
"""

def check_insurance(insurance_id):

    if not insurance_id:
        return {"insured":False}

    return {
        "insured":True,
        "provider":"national_health_insurance",
        "status":"pending_verification"
    }

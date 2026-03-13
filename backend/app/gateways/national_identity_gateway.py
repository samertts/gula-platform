"""
Gateway placeholder for Iraqi National ID system
(Prepared for future Ministry of Interior API integration)
"""

def verify_national_id(national_id):

    if len(national_id) not in [12,16]:
        return {"valid":False}

    return {
        "valid":True,
        "source":"local_validation",
        "message":"Awaiting government registry integration"
    }

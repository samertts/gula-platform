"""
Interface layer for laboratory analyzers
HL7 / ASTM / LIS integration
"""

def receive_device_result(sample_id,test,value):

    return {
        "sample":sample_id,
        "test":test,
        "value":value,
        "status":"received"
    }

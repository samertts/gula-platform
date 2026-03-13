from tracker_engine import complete_sample

def device_result(sample_id, result):

    print("Device finished analysis:", sample_id)

    complete_sample(sample_id)

    print("Result ready")

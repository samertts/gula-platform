from health_record_engine.record_reader import get_patient_history


def load_patient_data(nhid):
    return get_patient_history(nhid)

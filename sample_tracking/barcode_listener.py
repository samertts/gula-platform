from tracker_engine import move_sample

def scan_barcode(sample_id, unit, device, operator):

    print("Barcode scanned:", sample_id)

    move_sample(sample_id, unit, device, operator)

    print("Sample moved automatically")

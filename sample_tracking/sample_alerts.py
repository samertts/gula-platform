from tracker_engine import detect_lost_samples

def check_alerts():

    lost = detect_lost_samples()

    if lost:

        print("ALERT: Possible lost samples")

        for s in lost:

            print("Sample not moved:", s)

from tracker_engine import detect_lost_samples


def check_alerts():

    lost = detect_lost_samples()

    if lost:


        for _s in lost:

            pass

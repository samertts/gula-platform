from lab_monitor import check_lab_status
from lab_selector import select_best_lab


def route_test_request(city):

    lab = select_best_lab(city)

    if lab:

        return {"assigned_lab": lab["name"]}

    return {"error": "no available lab"}


def network_health():

    return check_lab_status()

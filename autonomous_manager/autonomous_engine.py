from corrective_actions import isolate_offline_labs, restart_service

from control_center.system_analysis import analyze_system


def autonomous_decision():

    report = analyze_system()

    actions = []

    if report["metrics"]["labs_offline"] > 3:

        if isolate_offline_labs():
            actions.append("Offline labs isolated")

    if report["metrics"]["errors"] > 20:

        restart_service("exchange_server")
        actions.append("Restarted exchange server")

    if report["metrics"]["warnings"] > 20:

        restart_service("device_engine")
        actions.append("Restarted device engine")

    if not actions:
        actions.append("No action required")

    return actions

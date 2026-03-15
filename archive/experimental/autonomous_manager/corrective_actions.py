from action_log import log_action

from network_orchestrator.lab_registry import load_labs, save_labs


def isolate_offline_labs():

    labs = load_labs()

    updated = False

    for lab in labs:

        if lab["status"] != "online":
            lab["status"] = "isolated"
            updated = True

    if updated:
        save_labs(labs)
        log_action("isolate_labs", "offline labs isolated")

    return updated


def restart_service(service_name):

    # محاكاة إعادة تشغيل خدمة
    log_action("restart_service", service_name)

    return True

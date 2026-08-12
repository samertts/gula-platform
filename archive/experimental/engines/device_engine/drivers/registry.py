# Registry لجميع تعريفات الأجهزة

DRIVERS = []


def register(driver):
    DRIVERS.append(driver)


def detect_device(data):
    for d in DRIVERS:
        try:
            if d.detect(data):
                return d
        except:
            pass
    return None

API_KEY = "LAB_PLATFORM_SECRET"


def verify_key(key):

    if key == API_KEY:
        return True

    return False

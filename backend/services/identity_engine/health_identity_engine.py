from ai_identity_matcher import find_similar
from citizen_registry import register_citizen


def create_health_id(name, phone, national_id):

    similar = find_similar(name, phone)

    if similar:
        return {"warning": "possible duplicate", "matches": similar}

    return register_citizen(name, phone, national_id)


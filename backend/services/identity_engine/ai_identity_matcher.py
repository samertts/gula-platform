from services.identity_engine.citizens_db import load_db


def find_similar(name, phone):

    db = load_db()

    matches = []

    for c in db:

        if name.lower() in c["name"].lower() or phone == c["phone"]:
            matches.append(c)

    return matches

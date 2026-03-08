from services.identity_engine.citizens_db import generate_nhid, load_db, save_db


def register_citizen(name, phone, national_id):

    db = load_db()

    for c in db:
        if c["national_id"] == national_id:
            return c

    nhid = generate_nhid()

    citizen = {"nhid": nhid, "name": name, "phone": phone, "national_id": national_id}

    db.append(citizen)

    save_db(db)

    return citizen

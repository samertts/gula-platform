from lab_registry import load_labs


def select_best_lab(city):

    labs = load_labs()

    candidates = []

    for lab in labs:

        if lab["city"] == city and lab["status"] == "online":

            candidates.append(lab)

    if not candidates:
        return None

    best = max(candidates, key=lambda x: x["capacity"])

    return best

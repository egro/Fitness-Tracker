def kg_to_lbs(kg):
    if kg is None:
        return None
    return round(float(kg) * 2.20462, 1)


def cm_to_inches(cm):
    if cm is None:
        return None
    return round(float(cm) * 0.393701, 1)


def convert_weight(user, weight_kg):
    if weight_kg is None:
        return None
    return kg_to_lbs(weight_kg)


def convert_length(user, cm):
    if cm is None:
        return None
    return cm_to_inches(cm)


def weight_unit(user):
    return "lbs"


def length_unit(user):
    return "in"


def km_to_miles(km):
    if km is None:
        return None
    return round(float(km) * 0.621371, 2)


def convert_distance(user, distance_km):
    if distance_km is None:
        return None
    return km_to_miles(distance_km)


def distance_unit(user):
    return "mi"

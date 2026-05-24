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
    if user.profile.units == "imperial":
        return kg_to_lbs(weight_kg)
    return weight_kg


def convert_length(user, cm):
    if cm is None:
        return None
    if user.profile.units == "imperial":
        return cm_to_inches(cm)
    return cm


def weight_unit(user):
    return "lbs" if user.profile.units == "imperial" else "kg"


def length_unit(user):
    return "in" if user.profile.units == "imperial" else "cm"

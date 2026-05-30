from django import template
from ..utils import convert_weight as cw, convert_length as cl, weight_unit as wu, length_unit as lu, kg_to_lbs, convert_distance as cd, distance_unit as du

register = template.Library()


@register.filter
def convert_wt(weight_kg, user):
    if weight_kg is None:
        return "-"
    return cw(user, weight_kg)


@register.filter
def to_lbs(weight_kg):
    if weight_kg is None:
        return "-"
    return kg_to_lbs(float(weight_kg))


@register.filter
def convert_len(cm, user):
    if cm is None:
        return "-"
    return cl(user, cm)


@register.filter
def convert_dist(distance_km, user):
    if distance_km is None:
        return None
    return cd(user, distance_km)


@register.simple_tag
def weight_unit_tag(user):
    return wu(user)


@register.simple_tag
def length_unit_tag(user):
    return lu(user)


@register.simple_tag
def distance_unit_tag(user):
    return du(user)

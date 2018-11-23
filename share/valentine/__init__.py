from isis.utils import format_number


def get_mass_literal(mass):
    return format_number(mass.n) + ' ' + mass.unit

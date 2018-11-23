from decimal import Decimal


def list_dec_to_float(ll, already_parsed=None):
    if already_parsed is None:
        already_parsed = list()
    for item in ll[:]:
        if isinstance(item, (dict, list)):
            if id(item) not in already_parsed:
                already_parsed.append(id(item))
                if isinstance(item, dict):
                    dec_to_float(item, already_parsed)
                elif isinstance(item, list):
                    list_dec_to_float(item, already_parsed)
        elif isinstance(item, Decimal):
            ll[ll.index(item)] = float(item)


def list_float_to_dec(ll, already_parsed=None):
    if already_parsed is None:
        already_parsed = list()
    for item in ll[:]:
        if isinstance(item, (dict, list)):
            if id(item) not in already_parsed:
                already_parsed.append(id(item))
                if isinstance(item, dict):
                    float_to_dec(item, already_parsed)
                elif isinstance(item, list):
                    list_float_to_dec(item, already_parsed)
        elif isinstance(item, float):
            ll[ll.index(item)] = round(Decimal(item), 6)


def dec_to_float(dd, already_parsed=None):
    if isinstance(dd, list):
        list_dec_to_float(dd, already_parsed)
    else:
        if already_parsed is None:
            already_parsed = list()
        for key, value in dd.items():
            if isinstance(value, (dict, list)):
                if id(value) not in already_parsed:
                    already_parsed.append(id(value))
                    if isinstance(value, dict):
                        dec_to_float(value, already_parsed)
                    elif isinstance(value, list):
                        list_dec_to_float(value, already_parsed)
            elif isinstance(value, Decimal):
                dd[key] = float(value)


def float_to_dec(dictionary, already_parsed=None):
    if isinstance(dictionary, list):
        list_float_to_dec(dictionary, already_parsed)
    else:
        if already_parsed is None:
            already_parsed = list()
        for key, value in dictionary.items():
            if isinstance(value, (dict, list)):
                if id(value) not in already_parsed:
                    already_parsed.append(id(value))
                    if isinstance(value, dict):
                        float_to_dec(value, already_parsed)
                    elif isinstance(value, list):
                        list_float_to_dec(value, already_parsed)
            elif isinstance(value, float):
                dictionary[key] = round(Decimal(value), 6)

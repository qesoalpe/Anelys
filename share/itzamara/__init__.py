
def key_to_sort_item(item):
    if 'description' in item and item.description is not None:
        return key_to_sort_item_description(item.description)
    else:
        return ''


def key_to_sort_item_description(description):
    description = description.lower().strip()
    if ')' in description:
        description = description[description.find(')') + 1:].strip() + description[:description.find(')')]
    return description

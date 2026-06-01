from django import template

register = template.Library()


@register.filter(name='get_item')
def get_item(dictionary, key):
    """
    Get an item from a dictionary using a key.
    Usage: {{ my_dict|get_item:key }}
    """
    if dictionary is None:
        return None
    return dictionary.get(key)


@register.filter(name='get_tuple_item')
def get_tuple_item(dictionary, key):
    """
    Get an item from a nested dictionary where the key is a tuple.
    This is useful for accessing timetable_grid[day][(start_time, end_time)]
    Usage: {{ my_dict|get_tuple_item:key }}
    """
    if dictionary is None:
        return None
    # Try direct access first
    result = dictionary.get(key)
    if result is not None:
        return result
    # Try to find matching tuple key
    for k, v in dictionary.items():
        if isinstance(k, tuple) and len(k) == 2:
            # Compare time objects
            if k[0] == key[0] and k[1] == key[1]:
                return v
    return None
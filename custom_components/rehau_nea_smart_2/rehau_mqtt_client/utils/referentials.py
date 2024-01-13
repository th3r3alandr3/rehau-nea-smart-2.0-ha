"""Referentials utilities."""

def get_by_value(value, referentials):
    """Retrieve the item from the referentials list based on the provided value.

    Args:
        value: The value to search for.
        referentials (list): The list of referentials.

    Returns:
        dict or None: The item from the referentials list, or None if not found.
    """
    return next((item for item in referentials if str(item['value']) == str(value)), None)


def replace_keys(input_object, referentials):
    """Replace the keys in the input_object dictionary based on the referentials list.

    Args:
        input_object (dict): The input dictionary.
        referentials (list): The list of referentials.

    Returns:
        dict: The modified input dictionary with replaced keys.
    """
    if not isinstance(input_object, dict):
        return input_object

    for key in list(input_object.keys()):
        if isinstance(input_object[key], list):
            if get_by_value(key, referentials):
                index = str(get_by_value(key, referentials)["index"])
                input_object[index] = [replace_keys(item, referentials) for item in input_object[key]]
                del input_object[key]
        elif isinstance(input_object[key], dict):
            if get_by_value(key, referentials):
                index = str(get_by_value(key, referentials)["index"])
                input_object[index] = replace_keys(input_object[key], referentials)
                del input_object[key]
        else:
            if get_by_value(key, referentials):
                index = str(get_by_value(key, referentials)["index"])
                input_object[index] = input_object[key]
                del input_object[key]

    return input_object

"""Helper function for saving data as JSON."""
import os
import json

def save_as_json(data, file_name):
    """Save the data as JSON to the specified file.

    Args:
        data: The data to be saved.
        file_name (str): The name of the file.

    Returns:
        None
    """
    data_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data"))
    os.makedirs(data_dir, exist_ok=True)
    file_path = os.path.join(data_dir, file_name)

    with open(file_path, "w") as file:
        json.dump(data, file)

def read_from_json(file_name) -> list:
    """Read the data from the specified file.

    Args:
        file_name (str): The name of the file.

    Returns:
        list: The data from the file.
    """
    data_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data"))
    file_path = os.path.join(data_dir, file_name)
    try:
        with open(file_path, "r") as file:
            data = json.load(file)
            if data is None:
                return []
            if not isinstance(data, list):
                return [data]
            return data
    except FileNotFoundError:
        return []

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

"""UUID Generator."""
import uuid


def generate_uuid() -> str:
    """Generate a UUID (Universally Unique Identifier).

    Returns:
        str: The generated UUID.
    """
    return str(uuid.uuid4())

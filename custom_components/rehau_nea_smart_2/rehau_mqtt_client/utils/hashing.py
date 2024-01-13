"""Hashing utilities for the MQTT component."""
import hashlib
import base64

async def sha256_hash(input_str):
    """Compute the SHA-256 hash of the input string.

    Args:
        input_str (str): The input string to be hashed.

    Returns:
        bytes: The SHA-256 hash digest.
    """
    hash_object = hashlib.sha256()
    hash_object.update(input_str.encode())
    return hash_object.digest()


def base64_url_encode(buffer):
    """Encode the provided buffer using URL-safe Base64 encoding.

    Args:
        buffer: The buffer to be encoded.

    Returns:
        str: The URL-safe Base64 encoded string.
    """
    return base64.urlsafe_b64encode(buffer).decode().rstrip("=")


async def convert_challenge(challenge):
    """Convert the challenge string to a URL-safe Base64 encoded SHA-256 hash.

    Args:
        challenge (str): The challenge string.

    Returns:
        str: The URL-safe Base64 encoded SHA-256 hash.
    """
    hash_result = await sha256_hash(challenge)
    result = base64_url_encode(hash_result)
    return result

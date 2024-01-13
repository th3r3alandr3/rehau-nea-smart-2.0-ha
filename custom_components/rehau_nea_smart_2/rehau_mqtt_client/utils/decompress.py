"""Decompression utilities for Rehau NEA Smart 2."""
from lzstring import LZString
import json
import base64


def decompress_utf16(data: str):
    """Decompress a UTF-16 encoded string using LZString library.

    Args:
        data (str): The UTF-16 encoded string to decompress.

    Returns:
        dict: The decompressed JSON object.

    """
    decoded_text = LZString.decompressFromUTF16(data)
    return json.loads(decoded_text)


def decode_base64(data: str):
    """Decode a base64 encoded string.

    Args:
        data (str): The base64 encoded string to decode.

    Returns:
        str: The decoded string.

    """
    decoded = base64.b64decode(data)
    return decoded.decode("utf-8")


def encode_base64(data: str):
    """Encode a string to base64.

    Args:
        data (str): The string to encode.

    Returns:
        str: The base64 encoded string.

    """
    dataBytes = data.encode("utf-8")
    encoded = base64.b64encode(dataBytes)
    return encoded.decode("utf-8")

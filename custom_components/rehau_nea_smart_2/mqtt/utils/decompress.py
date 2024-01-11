from lzstring import LZString
import json
import base64


def decompress_utf16(data: str):
    decoded_text = LZString.decompressFromUTF16(data)
    return json.loads(decoded_text)


def decode_base64(data: str):
    decoded = base64.b64decode(data)
    return decoded.decode("utf-8")


def encode_base64(data: str):
    dataBytes = data.encode("utf-8")
    encoded = base64.b64encode(dataBytes)
    return encoded.decode("utf-8")

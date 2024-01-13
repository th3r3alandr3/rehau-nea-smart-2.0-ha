"""This module provides functions for compressing and decompressing strings using the LZString algorithm.

The LZString algorithm is a simple and efficient method for compressing and decompressing strings. It uses a combination of dictionary-based compression and variable-length encoding.

Functions:
- getBaseValue: Get the base value of a character in a given alphabet.
- _compress: Compress a string using the LZString algorithm.
- _decompress: Decompress a compressed string using the LZString algorithm.

Classes:
- Object: A simple class for storing key-value pairs.

Note: This module is based on the work of Marcel Dancak and is licensed under the Do What The Fuck You Want To Public License, Version 2.
"""

import math


keyStrBase64 = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/="
keyStrUriSafe = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+-$"
baseReverseDic = {}


class Object:
    """A generic object with dynamically assigned attributes."""

    def __init__(self, **kwargs):
        """Initialize the object with the given attributes.

        Args:
            **kwargs: Arbitrary keyword arguments representing attribute-value pairs.
        """
        for k, v in kwargs.items():
            setattr(self, k, v)


def getBaseValue(alphabet, character):
    """Get the base value of a character in the given alphabet.

    Args:
    alphabet (str): The alphabet used for encoding.
    character (str): The character to get the base value of.

    Returns:
    int: The base value of the character in the alphabet.
    """
    if alphabet not in baseReverseDic:
        baseReverseDic[alphabet] = {}
        for index, i in enumerate(alphabet):
            baseReverseDic[alphabet][i] = index
    return baseReverseDic[alphabet][character]


def _compress(uncompressed, bitsPerChar, getCharFromInt):
    """Compresses the given uncompressed string using the LZString algorithm.

    Args:
        uncompressed (str): The string to be compressed.
        bitsPerChar (int): The number of bits per character.
        getCharFromInt (function): A function that converts an integer to a character.

    Returns:
        str: The compressed string.
    """
    if uncompressed is None:
        return ""

    context_dictionary = {}
    context_c = ""
    context_w = ""
    context_data = []
    context_data_val = 0
    context_data_position = 0

    for context_c in uncompressed:
        if context_c not in context_dictionary:
            context_dictionary[context_c] = len(context_dictionary) + 1
            context_data.append(getCharFromInt(context_dictionary[context_c]))
        else:
            context_w += context_c

        context_data_val = (context_data_val << bitsPerChar) | context_dictionary[context_c]
        context_data_position += bitsPerChar

        while context_data_position >= 8:
            context_data.append(getCharFromInt(context_data_val & 0xFF))
            context_data_val >>= 8
            context_data_position -= 8

    # Flush the last character
    if context_data_position > 0:
        context_data.append(getCharFromInt(context_data_val & ((1 << context_data_position) - 1)))

    return ''.join(context_data)

def _decompress(length, resetValue, getNextValue):
    def get_next_bits(num_bits, data, resetValue, getNextValue):
        bits = 0
        maxpower = 2 ** num_bits
        power = 1
        while power != maxpower:
            resb = data.val & data.position
            data.position >>= 1
            if data.position == 0:
                data.position = resetValue
                data.val = getNextValue(data.index)
                data.index += 1
            bits |= power if resb > 0 else 0
            power <<= 1
        return bits

    dictionary = {i: i for i in range(3)}
    enlargeIn = 4
    dictSize = 4
    numBits = 3
    result = []

    data = Object(
        val=getNextValue(0),
        position=resetValue,
        index=1
    )

    next = get_next_bits(2, data, resetValue, getNextValue)
    if next == 0:
        c = chr(get_next_bits(8, data, resetValue, getNextValue))
    elif next == 1:
        c = chr(get_next_bits(16, data, resetValue, getNextValue))
    elif next == 2:
        return ""

    dictionary[3] = c
    w = c
    result.append(c)

    while True:
        if data.index > length:
            return ""

        c = get_next_bits(numBits, data, resetValue, getNextValue)

        if c == 0:
            c = dictSize
            dictionary[dictSize] = chr(get_next_bits(8, data, resetValue, getNextValue))
            dictSize += 1
            enlargeIn -= 1
        elif c == 1:
            c = dictSize
            dictionary[dictSize] = chr(get_next_bits(16, data, resetValue, getNextValue))
            dictSize += 1
            enlargeIn -= 1
        elif c == 2:
            return "".join(result)

        if enlargeIn == 0:
            enlargeIn = 2 ** numBits
            numBits += 1

        if c in dictionary:
            entry = dictionary[c]
        else:
            if c == dictSize:
                entry = w + w[0]
            else:
                return None
        result.append(entry)

        dictionary[dictSize] = w + entry[0]
        dictSize += 1
        enlargeIn -= 1

        w = entry
        if enlargeIn == 0:
            enlargeIn = 2 ** numBits
            numBits += 1


class LZString:
    """LZ-based compression algorithm for JavaScript."""

    def __init__(self):
        """Initialize the LZString object."""
        pass

    @staticmethod
    def compress(uncompressed):
        """Compresses the given string using LZString algorithm.

        Args:
            uncompressed (str): The string to be compressed.

        Returns:
            str: The compressed string.
        """
        return _compress(uncompressed, 16, chr)

    @staticmethod
    def compressToUTF16(uncompressed):
        """Compresses the given string to UTF-16 format.

        Args:
            uncompressed (str): The string to be compressed.

        Returns:
            str: The compressed string in UTF-16 format.
        """
        if uncompressed is None:
            return ""
        return _compress(uncompressed, 15, lambda a: chr(a+32)) + " "

    @staticmethod
    def compressToBase64(uncompressed):
        """Compresses the given input string using LZString algorithm and returns the compressed string encoded in Base64.

        Args:
            uncompressed (str): The input string to be compressed.

        Returns:
            str: The compressed string encoded in Base64.

        """
        if uncompressed is None:
            return ""
        res = _compress(uncompressed, 6, lambda a: keyStrBase64[a])
        # To produce valid Base64
        end = len(res) % 4
        if end > 0:
            res += "="*(4 - end)
        return res

    @staticmethod
    def compressToEncodedURIComponent(uncompressed):
        """Compresses the given string using LZString algorithm and returns the compressed string as an encoded URI component.

        Args:
            uncompressed (str): The string to be compressed.

        Returns:
            str: The compressed string as an encoded URI component.

        """
        if uncompressed is None:
            return ""
        return _compress(uncompressed, 6, lambda a: keyStrUriSafe[a])

    @staticmethod
    def decompress(compressed):
        """Decompresses a compressed string using LZString algorithm.

        Args:
            compressed (str): The compressed string to be decompressed.

        Returns:
            str: The decompressed string.

        Raises:
            None

        """
        if compressed is None:
            return ""
        if compressed == "":
            return None
        return _decompress(len(compressed), 32768, lambda index: ord(compressed[index]))

    @staticmethod
    def decompressFromUTF16(compressed):
        """Decompresses a compressed string in UTF-16 format using LZString algorithm.

        Args:
            compressed (str): The compressed string in UTF-16 format to be decompressed.

        Returns:
            str: The decompressed string.

        Raises:
            None

        """
        if compressed is None:
            return ""
        if compressed == "":
            return None
        return _decompress(len(compressed), 16384, lambda index: ord(compressed[index]) - 32)

    @staticmethod
    def decompressFromBase64(compressed):
        """Decompresses a compressed string encoded in Base64 using LZString algorithm.

        Args:
            compressed (str): The compressed string encoded in Base64 to be decompressed.

        Returns:
            str: The decompressed string.

        Raises:
            None

        """
        if compressed is None:
            return ""
        if compressed == "":
            return None
        return _decompress(len(compressed), 32, lambda index: getBaseValue(keyStrBase64, compressed[index]))

    @staticmethod
    def decompressFromEncodedURIComponent(compressed):
        """Decompresses a compressed string as an encoded URI component using LZString algorithm.

        Args:
            compressed (str): The compressed string as an encoded URI component to be decompressed.

        Returns:
            str: The decompressed string.

        Raises:
            None

        """
        if compressed is None:
            return ""
        if compressed == "":
            return None
        compressed = compressed.replace(" ", "+")
        return _decompress(len(compressed), 32, lambda index: getBaseValue(keyStrUriSafe, compressed[index]))

    @staticmethod
    def decompressFromUint8Array(compressed):
        """Decompresses a compressed Uint8Array using LZString algorithm.

        Args:
            compressed (list): The compressed Uint8Array to be decompressed.

        Returns:
            str: The decompressed string.

        Raises:
            None

        """
        length_compressed = len(compressed)//2
        buf=[]
        for i in range(length_compressed):
            buf.append(compressed[i*2]*256+compressed[i*2+1])
        result=[]
        for i in buf:
            result.append(chr(i & 0xffff))
        return _decompress(''.join(result))

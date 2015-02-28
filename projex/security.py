"""
Encryption module for encrypting and testing information. If you want to
properly use this module for safest encryption, you will need to download
the PyCrypto module.
"""

import base64
import hashlib
import logging
import os.path
import random
import struct

logger = logging.getLogger(__name__)

import projex.text
from .text import nativestring as nstr


try:
    from Crypto.Cipher import AES
    from Crypto.PublicKey import RSA
    from Crypto import Random

except ImportError:
    warn = 'The PyCrypto module was not found.  It is highly recommended for ' \
           'security purposes to download and install this module for use ' \
           ' with the security module.'

    logger.warning(warn)
    AES = None
    Random = None
    RSA = None

# ----------------------------------------------------------------------
#                              FUNCTIONS
# ---------------------------------------------------------------------


def check(a, b):
    """
    Checks to see if the two values are equal to each other.
    
    :param      a | <str>
                b | <str>
    
    :return     <bool>
    """
    aencrypt = encrypt(a)
    bencrypt = encrypt(b)

    return a == b or a == bencrypt or aencrypt == b


def decodeBase64(text, encoding='utf-8'):
    """
    Decodes a base 64 string.
    
    :param      text | <str>
                encoding | <str>
    
    :return     <str>
    """
    text = projex.text.toBytes(text, encoding)
    return projex.text.toUnicode(base64.b64decode(text), encoding)


def decrypt(text, key=None):
    """
    Decrypts the inputted text using the inputted key.
    
    :param      text    | <str>
                key     | <str>
    
    :return     <str>
    """
    if key is None:
        key = ENCRYPT_KEY

    bits = len(key)
    text = base64.b64decode(text)
    iv = text[:16]
    cipher = AES.new(key, AES.MODE_CBC, iv)
    return unpad(cipher.decrypt(text[16:]))


def decryptfile(filename, key=None, outfile=None, chunk=64 * 1024):
    """
    Decrypts a file using AES (CBC mode) with the given key.  If no
    file is supplied, then the inputted file will be modified in place.
    The chunk value will be the size with which the function uses to
    read and encrypt the file.  Larger chunks can be faster for some files
    and machines.  The chunk MUST be divisible by 16.
    
    :param      text    | <str>
                key     | <str>
                outfile | <str> || None
                chunk   | <int>
    """
    if key is None:
        key = ENCRYPT_KEY

    if not outfile:
        outfile = os.path.splitext(filename)[0]

    with open(filename, 'rb') as input:
        origsize = struct.unpack('<Q', input.read(struct.calcsize('Q')))[0]
        iv = input.read(16)
        cipher = AES.new(key, AES.MODE_CBC, iv)

        with open(outfile, 'wb') as output:
            while True:
                data = input.read(chunk)
                if len(data) == 0:
                    break

                data = cipher.decrypt(data)
                data = unpad(data)
                output.write(data)
                output.truncate(origsize)


def encodeBase64(text, encoding='utf-8'):
    """
    Decodes a base 64 string.
    
    :param      text | <str>
                encoding | <str>
    
    :return     <str>
    """
    text = projex.text.toBytes(text, encoding)
    return base64.b64encode(text)


def encrypt(text, key=None):
    """
    Encrypts the inputted text using the AES cipher.  If the PyCrypto
    module is not included, this will simply encode the inputted text to
    base64 format.
    
    :param      text    | <str>
                key     | <str>
    
    :return     <str>
    """
    if key is None:
        key = ENCRYPT_KEY

    bits = len(key)
    text = pad(text, bits)
    iv = Random.new().read(16)
    cipher = AES.new(key, AES.MODE_CBC, iv)
    return base64.b64encode(iv + cipher.encrypt(text))


def encryptfile(filename, key=None, outfile=None, chunk=64 * 1024):
    """
    Encrypts a file using AES (CBC mode) with the given key.  If no
    file is supplied, then the inputted file will be modified in place.
    The chunk value will be the size with which the function uses to
    read and encrypt the file.  Larger chunks can be faster for some files
    and machines.  The chunk MUST be divisible by 16.
    
    :param      text    | <str>
                key     | <str>
                outfile | <str> || None
                chunk   | <int>
    """
    if key is None:
        key = ENCRYPT_KEY

    if not outfile:
        outfile = filename + '.enc'

    iv = Random.new().read(16)
    cipher = AES.new(key, AES.MODE_CBC, iv)
    filesize = os.path.getsize(filename)

    with open(filename, 'rb') as input:
        with open(outfile, 'wb') as output:
            output.write(struct.pack('<Q', filesize))
            output.write(iv)

            while True:
                data = input.read(chunk)
                if len(data) == 0:
                    break

                data = pad(data, len(key))
                output.write(cipher.encrypt(data))


def generateKey(password, bits=32):
    """
    Generates a new encryption key based on the inputted password.
    
    :param      password    | <str>
                bits        | <int>  | 16 or 32 bits
    
    :return     <str>
    """
    if bits == 32:
        hasher = hashlib.sha256
    elif bits == 16:
        hasher = hashlib.md5
    else:
        raise StandardError('Invalid hash type')

    return hasher(password).digest()


def generateToken(bits=32):
    """
    Generates a random token based on the given parameters.
    
    :return     <str>
    """
    if bits == 64:
        hasher = hashlib.sha256
    elif bits == 32:
        hasher = hashlib.md5
    else:
        raise StandardError('Unknown bit level.')
    return hasher(nstr(random.getrandbits(256))).hexdigest()


def pad(text, bits=32):
    """
    Pads the inputted text to ensure it fits the proper block length
    for encryption.
    
    :param      text | <str>
                bits | <int>
    
    :return     <str>
    """
    return text + (bits - len(text) % bits) * chr(bits - len(text) % bits)


def unpad(text):
    """
    Unpads the text from the given block size.
    
    :param      text | <str>
    
    :return     <str>
    """
    return text[0:-ord(text[-1])]

# applications that use encryption should define their own encryption key
# and assign it to this value - this will need to be the same size as the
# block size.  by default, just setting the encryption key as 'password'
# THIS SHOULD BE RESET FOR YOUR APPLICATION
ENCRYPT_KEY = generateKey('password')


import getpass
import hashlib


def acquire_key():
    key_unicode = getpass.getpass()
    return key_unicode


def get_key():
    unicode_key = acquire_key()
    return hashlib.sha256(unicode_key.encode("utf-8")).digest()

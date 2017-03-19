import getpass
import hashlib


def acquire_key():
    key_unicode = getpass.getpass()
    return key_unicode


def get_key_stream(unicode_key, nonce, seqnum):
    keyhash = hashlib.sha256(unicode_key.encode("utf-8")).hexdigest()
    secretstring = "%d%s%d" % (nonce, keyhash, seqnum)
    return hashlib.sha256(secretstring.encode("utf-8")).digest()


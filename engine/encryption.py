

def encrypt_decrypt(bytestream, key):
    for i in range(len(bytestream)):
        bytestream[i] = bytestream[i] ^ key[i % len(key)]
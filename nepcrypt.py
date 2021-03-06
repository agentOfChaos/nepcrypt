import argparse
import os
import sys
import bitarray
import secrets
import struct

from engine import huffman, key_routine, encryption


block_size = 20 * 1024


"""
    Simple block cipher algorithm designed by me, following the principles of "confusion" and "diffusion"
    The file is first compressed using huffman coding, and then encrypted by xor-ing it to the keystream.
    The keystream is obtained by repeating the 32 bytes generated by hashing the password.
"""


def parsecli():
    parser = argparse.ArgumentParser(description="Encrypt and Decrypt a file using a symmetric cipher invented by "
                                                 "yours truly.")

    parser.add_argument('input', help='plaintext to encrypt / ciphertext to decrypt', type=str)
    parser.add_argument('output', help='generated cipher / message', type=str)
    parser.add_argument('-d', '--decrypt', help='decrypt (default is to encrypt)', action='store_true')
    parser.add_argument('--just-compress', help='(debug purposes) run the compression pass, but skip the'
                                                ' encryption pass', action='store_true')

    return parser.parse_args()


def encrypt_block(block, key, seqnum, nonce, just_compress=False):
    bitblob = huffman.compress(block)
    bytelist = bytearray(bitblob.tobytes())

    if just_compress:
        return bytelist, seqnum + 1

    keystream = key_routine.get_key_stream(key, nonce, seqnum)
    encryption.encrypt_decrypt(bytelist, keystream)
    return bytelist, seqnum + 1


def decrypt_block(block, key, seqnum, nonce, just_compress=False):
    bytelist = bytearray(block)
    keystream = key_routine.get_key_stream(key, nonce, seqnum)

    if not just_compress:
        encryption.encrypt_decrypt(bytelist, keystream)

    bitblob = bitarray.bitarray(endian="big")
    bitblob.frombytes(bytes(bytelist))

    return huffman.uncompress(bitblob), seqnum + 1


def encrypt(cli):
    with open(cli.input, "rb") as loadfile:
        with open(cli.output, "wb") as savefile:
            nonce = secrets.randbelow(sys.maxsize)
            seqnum = 0
            key = key_routine.acquire_key()
            if not cli.just_compress:
                savefile.write(struct.pack("Q", nonce))
            while True:
                block = loadfile.read(block_size)
                if len(block) == 0:
                    break
                encrypted, seqnum = encrypt_block(block, key, seqnum, nonce, just_compress=cli.just_compress)
                savefile.write(encrypted)


def decrypt(cli):
    with open(cli.input, "rb") as loadfile:
        with open(cli.output, "wb") as savefile:
            if cli.just_compress:
                nonce = 0
            else:
                nonce = struct.unpack("Q", loadfile.read(8))[0]
            seqnum = 0
            key = key_routine.acquire_key()
            while True:
                block = loadfile.read(block_size)
                if len(block) == 0:
                    break
                decrypted, seqnum = decrypt_block(block, key, seqnum, nonce, just_compress=cli.just_compress)
                savefile.write(decrypted)



if __name__ == "__main__":
    cli = parsecli()
    if cli.decrypt:
        decrypt(cli)
    else:
        encrypt(cli)

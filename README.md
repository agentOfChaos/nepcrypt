# nepcrypt
Toy block cipher

# how it works

1. the file is compressed with huffman coding
2. the password is hashed and the hash is repeated to form the keystream
3. the compressed-file's bytes are xor-ed to the keystream

# usage example

    python nepcrypt.py topsecret.txt cipher.dat

    python nepcrypt.py -d cipher.dat message.txt
    
# bonus

To compute the entropy of a file:

    python entro.py yourfile.bin

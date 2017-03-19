import argparse
import math


def parsecli():
    parser = argparse.ArgumentParser(description="Simple tool to calculate the entropy of a file")

    parser.add_argument('file', help='file containing data', type=str)

    return parser.parse_args()


def compute_entropy(data):
    bytecount = {}
    entropy = 0.0
    total_length = float(len(data))

    def increment(byte):
        try:
            bytecount[byte] += 1.0
        except KeyError:
            bytecount[byte] = 1.0

    def get_count(byte):
        try:
            return bytecount[byte]
        except KeyError:
            return 0.0

    def get_factor(byte):
        if get_count(byte) == 0.0:
            return 0.0
        p_i = get_count(byte) / total_length
        return p_i * math.log2(p_i)

    for byte in data:
        increment(byte)

    for i in range(256):
        entropy -= get_factor(i)

    return entropy


def print_entropy(data):
    print("Entropy of random data:\t8")
    print("Entropy of your file:\t%f" % compute_entropy(data))


if __name__ == "__main__":
    cli = parsecli()

    with open(cli.file, "rb") as file:
        filedata = file.read()
        print_entropy(filedata)
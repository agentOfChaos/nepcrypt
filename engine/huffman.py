import bitarray
import struct
import math


"""
    The original purpose of this code was to decompress the data files from the
    game "Hyperdimension Neptunia Re;Birth 2 (steam edition)", thus, the name "nepcrypt".
    Funny enough, I first learnt about huffman coding while hacking a jrpg
    about cute animegirls.

    For informations about how the actual algorithm works, see https://en.wikipedia.org/wiki/Huffman_coding
"""


class TreeNode:

    def __init__(self):
        self.childzero = None   # if I'm ever having children, I'll name them like this
        self.childone = None
        self.isleaf = False     # to let the algorithm know when to stop
        self.isActive = True    # active node: a subtree can be attached here
        self.value = b"\0"       # value (a single byte)

    def set_value(self, value):
        self.isActive = False
        self.isleaf = True
        self.value = value

    def expand_node(self):
        """ append a left (zero) and right (one) child, left is returned """
        return self.bilateral_expand()[0]

    def bilateral_expand(self):
        """ append a left (zero) and right (one) child, return a list containing both """
        self.isActive = False
        self.isleaf = False
        self.childzero = TreeNode()
        self.childone = TreeNode()
        return [self.childzero, self.childone]

    def find_first_active(self):
        """ recursive depth-first search for the leftmost active node """
        if self.isleaf:
            return None
        if self.isActive:
            return self
        if self.childzero.isActive:
            return self.childzero
        deepleft = self.childzero.find_first_active()
        if deepleft is not None:
            return deepleft
        if self.childone.isActive:
            return self.childone
        deepright = self.childone.find_first_active()
        if deepright is not None:
            return deepright
        return None


def tree2dot(root, filename):
    seen_nodes = []

    def traversal(node):
        seen_nodes.append(node)
        if not node.isleaf:
            traversal(node.childzero)
            traversal(node.childone)

    traversal(root)
    with open(filename, "w") as tfile:
        tfile.write("digraph yggdrasil {\n")
        for node in seen_nodes:
            tfile.write("node_" + str(seen_nodes.index(node)))
            if node.isleaf:
                tfile.write(" [label=\"%x\"]" % struct.unpack("B", node.value))
            else:
                tfile.write(" [label=\"\"]")
            tfile.write("\n")
        for node in seen_nodes:
            if not node.isleaf:
                tfile.write("node_" + str(seen_nodes.index(node)) + " -> node_" + str(seen_nodes.index(node.childzero)) +
                            " [label=0]\n")
                tfile.write("node_" + str(seen_nodes.index(node)) + " -> node_" + str(seen_nodes.index(node.childone)) +
                            " [label=1]\n")
        tfile.write("}\n")


def buildtree(root, cursor, bitstream):
    while True:
        # get the active node to work on
        worknode = root.find_first_active()
        if worknode is None:  # if the tree is completely built, then stop
            break
        # read the 'spacers'
        downleft_distance = 0
        try:
            while bitstream[cursor]:
                downleft_distance += 1
                cursor += 1
        except IndexError:
            print("Tree parsing aborted: cursor at HEADER + %x, bit #%d" % (math.floor(cursor/8), cursor % 8))
            return None, None
        cursor += 1
        # read the byte
        value = bitstream[cursor:cursor+8].tobytes()
        cursor += 8
        for i in range(downleft_distance):
            worknode = worknode.expand_node()
        worknode.set_value(value)
    return root, cursor


def uncompress(bitstream, debuggy=False):
    cursor = 0
    root = TreeNode()
    byte_list = []

    root, cursor = buildtree(root, cursor, bitstream)
    if root is None:
        print("Tree construction failed, exiting")
        return bytes()

    if debuggy:
        print("Tree parsing finished: cursor at %x, bit #%d" % (math.floor(cursor/8), cursor % 8))
        tree2dot(root, "debugtree.dot")

    while True:
        tarzan = root
        while not tarzan.isleaf:
            try:
                chu = bitstream[cursor]
            except IndexError:
                return bytes(byte_list)
            cursor += 1
            if chu == False:
                tarzan = tarzan.childzero
            else:
                tarzan = tarzan.childone
        byte_list.append(ord(tarzan.value))


def collectBytes(Lb, multib, block):
    for readbyte_int in block:
        readbyte = struct.pack("B", readbyte_int)
        if readbyte not in Lb:
            Lb.append(readbyte)
            multib[readbyte] = 1
        else:
            multib[readbyte] += 1


def buildHuffmanTree(block):
    Lb = []
    multib = {}
    nodemap = []
    def keyfun(elem):
        return multib[elem]
    collectBytes(Lb, multib, block)
    Lb = sorted(Lb, key=keyfun)

    for b in Lb:
        nn = TreeNode()
        nn.set_value(b)
        nodemap.append((b, nn, multib[b]))

    while len(nodemap) > 1:
        uno = nodemap.pop(0)
        due = nodemap.pop(0)
        radix = TreeNode()
        radix.childzero = uno[1]
        radix.childone = due[1]
        newcost = uno[2] + due[2]
        i = 0
        while i < len(nodemap):
            if nodemap[i][2] > newcost:
                break
            i += 1
        nodemap.insert(i, (0, radix, newcost))

    return nodemap[0][1]


def compress(block, debuggy=False):
    """ :return: bitarray object containing the compressed data """
    lookup_table = {}
    vecbuild_path = bitarray.bitarray(endian="big")
    out_bitstream = bitarray.bitarray(endian="big")

    def build_lookup_table(node, path, search):
        if not node.isleaf:
            lefty = path.copy()
            lefty.append(False)
            righty = path.copy()
            righty.append(True)
            build_lookup_table(node.childzero, lefty, search)
            build_lookup_table(node.childone, righty, search)
        elif node.value == search:
            lookup_table[search] = path

    def build_vector_tree(node):
        if node.isleaf:
            vecbuild_path.append(False)
            out_bitstream.extend(vecbuild_path)
            for i in range(len(vecbuild_path)): vecbuild_path.pop()
            val = bitarray.bitarray(endian="big")
            val.frombytes(node.value)
            out_bitstream.extend(val)
        else:
            vecbuild_path.append(True)
            build_vector_tree(node.childzero)
            build_vector_tree(node.childone)

    tree = buildHuffmanTree(block)

    if debuggy:
        tree2dot(tree, "optimumtree.dot")

    build_vector_tree(tree)

    for datum_int in block:
        datum = struct.pack("B", datum_int)
        if datum not in lookup_table.keys():
            build_lookup_table(tree, bitarray.bitarray(endian="big"), datum)
        out_bitstream.extend(lookup_table[datum])

    return out_bitstream

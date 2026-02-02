'''Script to create Cannonical Huffman Tree per https://www.geeksforgeeks.org/dsa/canonical-huffman-coding/
Updates to take string input and return list of bit lengths
'''
import heapq
from collections import defaultdict

# Node class to store data and its frequency
class Node:
    def __init__(self, char, freq):
        self.char = char
        self.freq = freq
        self.left = None
        self.right = None

    # Defining comparators less_than and equals
    def __lt__(self, other):
        return self.freq < other.freq

    def __eq__(self, other):
        if(other == None):
            return False
        if(not isinstance(other, Node)):
            return False
        return self.freq == other.freq

# Function to generate Huffman codes
def code_gen(root, code_length, code_map):
    if root is None:
        return

    if root.left is None and root.right is None:
        code_map[len(code_length)].append(root.char)

    code_gen(root.left, code_length + '0', code_map)
    code_gen(root.right, code_length + '1', code_map)

# Main function implementing Huffman coding
def cannonicalHuffman(string):
    # Priority queue to store heap tree

    frequencies = getFrequency(string) 
    q = [Node(char, freq) for char, freq in zip(frequencies.keys(), frequencies.values())]
    heapq.heapify(q)

    while len(q) > 1:
        left = heapq.heappop(q)
        right = heapq.heappop(q)

        merged = Node(None, left.freq + right.freq)
        merged.left = left
        merged.right = right

        heapq.heappush(q, merged)

    root = heapq.heappop(q)
    code_map = defaultdict(list)
    code_gen(root, "", code_map)

    # Generate Canonical Huffman codes
    canonical_map = {}
    c_code = 0
    for length in sorted(code_map.keys()):
        for char in sorted(code_map[length]):
            canonical_map[char] = bin(c_code)[2:].zfill(length)
            c_code += 1
        c_code <<= 1

    print(canonical_map)

    lengths = []
    # Print Canonical Huffman codes
    for i in range(0, 256):
        if chr(i) in canonical_map:
            lengths.append(len(canonical_map[chr(i)]))

        else:
            lengths.append(0)

    # for char in sorted(canonical_map):
    #     lengths.append(len(canonical_map[char]))

    return lengths

def getFrequency(string: str) -> dict: 
    '''
    Calculates frequency of each character in strig
    
    :param string: string to get count characters from
    :type string: str
    :return: dictionary with character-frequency pairs
    :rtype: dict
    '''
    frequencies = {}
    for char in string: 
        if char in frequencies:
            frequencies[char] += 1

        else: 
            frequencies[char] = 1

    return frequencies

# Driver code
if __name__ == "__main__":
    test_string = "aaabbbbccd"
    cannonicalHuffman(test_string)
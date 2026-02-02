"""
Script to create a length limited cannonical huffman encoding 

Uses Package Merge to create length limited huffman encoding. Then bottom up greedily creates canonical encoding. 
"""

from typing import List 

from huffman.packageMerge import packageMerge, Item

def lengthLimitedCannonicalHuffman(frequencies) -> dict:
    '''
    Creates length limited huffman encoding 

    :param string: string for encoding to be based on
    :type string: str
    :return: list of lengths for each character (285)
    :rtype: dict
    '''
    n = len(frequencies)
    I = []
    L = 15

    for key in frequencies:
        for l in range(1, L+1):
            I.append(Item(2**(-l), frequencies[key], key))

    S = packageMerge(I, n-1)

    h = []

    for key in frequencies:
        count = 0
        for item in S: 
            if key == item.label: 
                count+=1 
        h.append(count)

    codeLengths = list(zip(frequencies.keys(), h))

    codeLengths.sort(key=lambda x: (x[1], x[0]))

    codes = [x[0] for x in codeLengths]
    lengths = [x[1] for x in codeLengths]

    lengths.append(lengths[-1]) # hack fix

    canonical_code = {}
    length_map = {}
    code = 0
    for id, key in enumerate(codes):
        canonical_code[key] = code
        length_map[key] = lengths[id] if lengths[id] != 0 else 1 # explore why this would ever be 0 (how can you have a code length of zero?)
         
        code = (code + 1) << (lengths[id+1] - lengths[id])

    print(canonical_code)
    print(length_map)

    return canonical_code, length_map

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

if __name__ == "__main__":
    string = "bbbbaaaccdd" # doesnt work since recounting uses frequency only. need to fix the counting somehow
    print(lengthLimitedCannonicalHuffman(getFrequency(string)))

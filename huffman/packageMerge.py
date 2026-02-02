'''
This script implements the package merge algorithm. 
Reference: https://ics.uci.edu/~dhirschb/pubs/LenLimHuff.pdf

Simplification: X is assumed to be a natural number (rather than positive diadic)
'''
from typing import List, Self, Tuple
from math import log2

class Item:
    def __init__(self, width, weight, label=None):
        self.width = width 
        self.weight = weight
        self.label = label
        self.children = [self]

    def package(self, other) -> Self:
        '''
        packcages item with another item 

        :param self: this item 
        :param other: the item to be packaged with this one 
        :return: the package
        :rtype: Self
        '''
        package = Item(self.width + other.width, self.weight + other.weight) 
        package.children = self.children + other.children 
        return package
    
    def __gt__(self, other) -> bool:
        return self.weight > other.weight
    
    def __str__(self):
        return f"{self.width, self.weight, self.label}"

def packageMerge(I: List[Item], X: int) -> List[Item]:
    '''
    Provides a minimum total weight solution to selecting items from a set I, such that their (integral powers of 2) widths sum to a diadic total width. 
    
    :param I: Set of items [width, weight], where width is a integral power of 2, weight is a real number
    :type I: List[int, int]
    :param X: Total width, Diadic real positive number  
    :type X: int
    :return: subset of I whose widths sum to X, with minimum total weight
    :rtype: List[int]
    '''
    S = []
    # intialise L_d lists, where each L_d contains items of width 2^d sorted by increasing weights
    # L = {d: [(width, weight)...], ...}
    L = {}
    for item in I: 
        width = item.width 
        weight = item.weight
        d = int(log2(width))
        
        if d in L: 
            L[d].append(item)

        else : 
            L[d] = [item]

    for ld in L: 
        L[ld].sort(key=lambda x: x.weight, reverse=True)

    while X > 0: 
        minwidth = min_diadic(X)

        if len(I) == 0: return None 
        
        else: 
            # minimum d such that L_d is not empty 
            d = min(L.keys())
            
            r = 2**d

            if r > minwidth: return None 
            elif r == minwidth: 
                item = L[d].pop() 
                
                S += item.children
                
                X-=minwidth

            P = PACKAGE(L[d])
            del L[d]
            if d+1 not in L: L[d+1] = []
            L[d+1] = MERGE(P, L[d+1])

    return S

def PACKAGE(Ld: List[Item]) -> List[Item]:
    '''
    Forms list by combining items in consecutive pairs, starting form lightest. 

    :param Ld: list of items of length 2^d
    :type Ld: List[Tuple[int, int]]
    :return: P_{d+1}, package formed by combining elements
    :rtype: List[Tuple[int, int]]
    '''
    P = []
    if len(Ld) % 2 == 1: del Ld[0] # TODO: fix logic

    for k in range(len(Ld)//2):
        P.append(Ld[2*k].package(Ld[2*k+1]))

    return P 

def MERGE(P: List[Item], L: List[Item]) -> List[Item]:
    '''
    Merges two sorted lists
    
    :param P: sorted list
    :type P: List[Tuple[int, int]]
    :param L: sorted list
    :type L: List[Tuple[int, int]]
    :return: sorted list, merge of P, L
    :rtype: List[Tuple[int, int]]
    '''
    output = []
    while P and L: 
        if P[0] > L[0]:
            output.append(P.pop(0))
        else:
            output.append(L.pop(0))

    return output + P + L

def min_diadic(X: int) -> int:
    '''
    Returns the smallest number in the diadic expansion of X
    
    :param X: Diadic number
    :type X: int

    :return: Smallest number in the diadic expansion of X 
    :rtype: int
    '''
    binrep = bin(X)

    for (i, d) in enumerate(reversed(binrep)):
        if d == '1': return 2**i

if __name__ == "__main__":
    items = [Item(1, 1), Item(1, 2), Item(1, 3), Item(2, -10), Item(2, 2), Item(2, 1)]
    X = 7

    list = packageMerge(items, X)

    for item in list:
        print(item)
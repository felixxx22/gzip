"""Implementation of Hashing with Chaining from geeksforgeeks (https://www.geeksforgeeks.org/dsa/c-program-hashing-chaining/)"""
from hash.HashTable import Hash

class SimpleChain(Hash):
    def __init__(self): 
        super().__init__() 

        self.table ={}

    def insert(self, key, value) -> int: 
        """
        Insert value into hash table

        :param key: value to be inserted into hashtable
        :return: true if collision, otherwise false 
        :rtype: bool
        """
        index = self.get_hash_index(key)

        if index not in self.table:
            self.table[index] = [value]
        else:
            self.table[index].append(value)

        return index if len(self.table[index]) > 1 else 0
    
    def get_hash_index(self, key) -> int:
        """
        Returns hash value for key of three bytes

        :param key: key to be hashed
        :return: hash index
        :rtype: int
        """
        return (key[0] << 16) | (key[1] << 8) | key[2]
    
if __name__ == "__main__":
    hash = SimpleChain()

    print(hash.insert([100, 101, 102]))
    print(hash.insert([100, 100, 103]))
    print(hash.insert([231, 100, 103]))

    print(hash.table)
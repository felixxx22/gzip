from abc import ABC, abstractmethod

class Hash(ABC):
    @abstractmethod
    def insert(self, key):
        pass

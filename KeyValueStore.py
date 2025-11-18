from ValueObject import ValueObject
from Eviction import Eviction
import time

class KeyValueStore:

    def __init__(self, Eviction: Eviction):
        self.store = {}
        self.limit = 100
        self.eviction = Eviction

    def set(self, key, value, expiresAt, objType, objEnc):
        self.store[key] = ValueObject(value, expiresAt, objType | objEnc)

        if len(self.store) > self.limit:
            self.eviction.evict(self.store)


    def get(self, key):
        valObj = self.store.get(key, None)
        if valObj is not None and valObj.expiresAt != -1 and valObj.expiresAt < int(time.time()):
            del self.store[key]
            return None
        return valObj

    def delete(self, key):
        if self.get(key) is not None:
            del self.store[key]
            return True
        return False
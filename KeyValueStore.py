from ValueObject import ValueObject
import time

class KeyValueStore:

    store = {}

    def __init__(self):
        self.store = {}

    def set(self, key, value, expiresAt):
        self.store[key] = ValueObject(value, expiresAt)

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
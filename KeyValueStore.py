from ValueObject import ValueObject

class KeyValueStore:

    store = {}

    def __init__(self):
        self.store = {}

    def set(self, key, value, expiresAt):
        self.store[key] = ValueObject(value, expiresAt)

    def get(self, key):
        return self.store.get(key, None)

    def delete(self, key):
        if self.get(key) is not None:
            del self.store[key]
            return True
        return False
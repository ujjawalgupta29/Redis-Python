class Eviction:

    def evict(self, store: dict):
        for key, value in list(store.items()):
            del store[key]
            print(f'evicted key: {key}')
            return


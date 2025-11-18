class Eviction:

    def __init__(self):
        self.evictionRatio = 0.40
        self.evictionLimit = 100

    def evict(self, store: dict):
        current_size = len(store)
        # Calculate target size (60% of limit to leave headroom)
        target_size = int(self.evictionLimit * 0.60)
        
        # Calculate how many keys to evict to reach target size
        evictCount = max(0, current_size - target_size)
        
        # If no eviction needed, return early
        if evictCount == 0:
            return
        
        # Evict keys - use .keys() not .items()
        for key in list(store.keys()):
            del store[key]
            evictCount = evictCount - 1
            if evictCount == 0:
                break



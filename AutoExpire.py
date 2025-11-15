import time
from KeyValueStore import KeyValueStore

class AutoExpire:
    def __init__(self, keyValueStore: KeyValueStore):
        self.cronFreq = 1
        self.lastCronTime = time.time()
        self.expireLimit = 10
        self.expireFrac = 0.25
        self.keyValueStore = keyValueStore

    def cron(self):
        if time.time() - self.lastCronTime > self.cronFreq:
            expKeysFrac = self.expireKeys()

            while expKeysFrac > self.expireFrac:
                expKeysFrac = self.expireKeys()


    def expireKeys(self):
        expiredKeys = 0
        for key, value in list(self.keyValueStore.store.items()):
            if value.expiresAt != -1 and value.expiresAt < int(time.time()):
                expiredKeys = expiredKeys + 1
                self.keyValueStore.delete(key)

            if expiredKeys == self.expireLimit:
                break
        print(f'expiredKeys: {expiredKeys}')
        return expiredKeys/self.expireLimit
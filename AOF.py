import time

class AOF:


    def dumpToFile(self, store: dict):
        aofPath = f"redis-{str(int(time.time()))}.aof"
        with open(aofPath, "w") as f:
            for key, valueObj in store.items():
                f.write(self.encode(f"SET {key} {valueObj.value}"))

    def encode(self, data):
        res = ""
        tokens = data.split(" ")
        for token in tokens:
            res = res + self.encodeString(token)
        return f"*{len(tokens)}\r\n{res}"


    def encodeString(self, data):
        return f"${len(data)}\r\n{data}\r\n"
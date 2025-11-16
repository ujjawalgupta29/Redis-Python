from RedisCmd import RedisCmd
import time
from KeyValueStore import KeyValueStore
from AOF import AOF


class CommandEvaluator:

    def __init__(self, keyValueStore: KeyValueStore):
        self.keyValueStore = keyValueStore
        self.aof = AOF()

    def evaluate(self, redisCmd: RedisCmd):
        cmd = redisCmd.cmd
        args = redisCmd.args

        if cmd == 'PING':
            return self.evaluatePing(args)
        elif cmd == 'SET':
            return self.evaluateSet(args)
        elif cmd == 'GET':
            return self.evaluateGet(args)
        elif cmd == 'TTL':
            return self.evaluateTtl(args)
        elif cmd == 'DEL':
            return self.evaluateDel(args)
        elif cmd == 'EXPIRE':
            return self.evaluateExpire(args)
        elif cmd == 'INCR':
            return self.evaluateIncr(args)
        elif cmd == 'BGREWRITEAOF':
            return self.evaluateBgRewriteAof()
        else:
            return '-ERR unknown command ' + cmd + '\r\n'

    def evaluatePing(self, args):
        if len(args) > 1:
            return "-ERR wrong number of arguments for 'ping' command\r\n"
        elif len(args) == 1:
            return self.encode(args[0], False)
        else:
            return self.encode("PONG")


    def evaluateSet(self, args):
        if len(args) <= 1:
            return "-ERR wrong number of arguments for 'set' command\r\n"
        key = args[0]
        value = args[1]
        expiresAt = -1

        i = 2
        while i < len(args):
            if args[i] == 'EX':
                i = i + 1
                if i < len(args):
                    ttl = int(args[i])
                    expiresAt = int(time.time()) + ttl
                else:
                    return "-ERR syntax error\r\n"
                i = i + 1
            else:
                return "-ERR syntax error\r\n"

        self.keyValueStore.set(key, value, expiresAt)
        return self.encode("OK")

    def evaluateGet(self, args):
        if len(args) != 1:
            return "-ERR wrong number of arguments for 'get' command\r\n"
        key = args[0]

        valueObj = self.keyValueStore.get(key)

        if valueObj is None:
            return "$-1\r\n"; # (nil)

        return self.encode(valueObj.value, False)

    def evaluateTtl(self, args):
        if len(args) != 1:
            return "-ERR wrong number of arguments for 'get' command\r\n"
        key = args[0]

        valueObj = self.keyValueStore.get(key)

        if valueObj is None:
            return ":-2\r\n"

        expiresAt = valueObj.expiresAt
        if expiresAt == -1:
            return ":-1\r\n"
        
        duration = expiresAt - int(time.time())
        if(duration < 0):
            return ":-2\r\n"
        return self.encode(duration, False)

    def encode(self, data, isSimple=True):
        if(type(data) == str):
            if isSimple:
                return '+' + data + '\r\n'
            else:
                return '$' + str(len(data)) + '\r\n' + data + '\r\n'
        elif(type(data) == int):
            return ':' + str(data) + '\r\n'
        else:
            return '-ERR unknown type: ' + str(type(data)) + '\r\n'


    def evaluateDel(self, args):
        deletedKeys = 0
        for key in args:
            if self.keyValueStore.delete(key):
                deletedKeys = deletedKeys + 1
        return self.encode(deletedKeys, False)

    def evaluateExpire(self, args):
        if len(args) != 2:
            return "-ERR wrong number of arguments for 'expire' command\r\n"
        key = args[0]
        obj = self.keyValueStore.get(key)
        if obj is None:
            return self.encode(0, False)
        
        ttl = int(args[1])

        obj.expiresAt = int(time.time()) + ttl
        return self.encode(1, False)

    def evaluateBgRewriteAof(self):
        print("Background append only file rewriting started")
        self.aof.dumpToFile(self.keyValueStore.store)
        return self.encode(" Background AOF rewrite finished successfully")

    def evaluateIncr(self, args):
        if len(args) != 1:
            return "-ERR wrong number of arguments for 'incr' command\r\n"
        key = args[0]
        obj = self.keyValueStore.get(key)
        if obj is None:
            self.keyValueStore.set(key, 0, -1)
            obj = self.keyValueStore.get(key)
        if type(obj.value) != int:
            return "-ERR value is not an integer or out of range\r\n"
        obj.value = int(obj.value) + 1
        return self.encode(obj.value, False)
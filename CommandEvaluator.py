from RedisCmd import RedisCmd

class CommandEvaluator:
    def evaluate(self, redisCmd: RedisCmd):
        cmd = redisCmd.cmd
        args = redisCmd.args

        if cmd == 'PING':
            return self.evaluatePing(args)
        else:
            return '-ERR unknown command ' + cmd + '\r\n'

    def evaluatePing(self, args):
        if len(args) > 1:
            return "-ERR wrong number of arguments for 'ping' command\r\n"
        elif len(args) == 1:
            return self.encode(args[0], False)
        else:
            return self.encode("PONG")

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
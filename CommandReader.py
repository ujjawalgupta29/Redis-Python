from RedisCmd import RedisCmd

class CommandReader:
    def readCommand(self, client_socket):
        data = client_socket.recv(1024)
        print(f"Raw data: {data}")
        data = data.decode('utf-8')
        print(f"Decoded data: {data}")

        tokens, _ = self.decodeCmd(data)
        print(f"Parsed tokens: {tokens}")
        if tokens and len(tokens) > 0:
            return RedisCmd(tokens[0], tokens[1:])
        return None

    def decodeCmd(self, data):
        if not data:
            return None, 0
            
        # Dictionary-based switch for RESP protocol
        switch_map = {
            '$': self.readBulkString,
            '*': self.readArray
        }
        
        handler = switch_map.get(data[0])
        if handler:
            return handler(data)
        else:
            return None, 0

    def readLength(self, data):
        length = 0
        for i in range(len(data)):
            if not (data[i] >= '0' and data[i] <= '9'):
                return length, i+2
            length = length * 10 + (ord(data[i]) - ord('0'))
        return -1, -1

    def readArray(self, data):
        pos = 1
        length, delta = self.readLength(data[pos:])
        if length == -1:
            return None, 0
        
        pos += delta

        tokens = []
        for i in range(length):
            token, delta = self.decodeCmd(data[pos:])
            if token is None:
                return None, 0
            pos += delta
            tokens.append(token)
        print(tokens)
        return tokens, pos

    def readBulkString(self, data):
        pos = 1
        length, delta = self.readLength(data[pos:])
        if length == -1:
            return None, 0
        pos += delta
        return data[pos:pos+length], pos+length+2
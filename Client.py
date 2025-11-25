class Client:
    def __init__(self, fd, isTxn, cmdQueue, socket):
        self.fd = fd
        self.isTxn = isTxn
        self.cmdQueue = cmdQueue
        self.socket = socket
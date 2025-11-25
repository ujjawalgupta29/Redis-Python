class Client:
    def __init__(self, fd, isTxn, cmdQueue, socket):
        self.fd = fd
        self.isTxn = isTxn
        self.cmdQueue = cmdQueue
        self.socket = socket

    def beginTxn(self):
        self.isTxn = True
        self.cmdQueue = []
        
    def endTxn(self):
        self.isTxn = False
        self.cmdQueue = []

    def isTxnRunning(self):
        return self.isTxn

    def addCmdToQueue(self, cmd):
        self.cmdQueue.append(cmd)

    def getCmdQueue(self):
        return self.cmdQueue
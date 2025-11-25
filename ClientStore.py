class ClientStore:
    def __init__(self):
        self.clients = {}

    def addClient(self, client):
        self.clients[client.fd] = client

    def removeClient(self, fd):
        del self.clients[fd]

    def getClient(self, fd):
        return self.clients.get(fd)
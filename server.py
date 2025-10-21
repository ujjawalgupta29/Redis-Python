import socket
from CommandReader import CommandReader
from CommandEvaluator import CommandEvaluator

#configs
conn_clients = 0
port = 7379
host = 'localhost'

#create a server socket
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((host, port))
server.listen(5) #max 5 conn will be queued

print(f'Server is running on port {port}')

command_reader = CommandReader()
command_evaluator = CommandEvaluator()

while True:
    client_socket, client_address = server.accept()
    conn_clients += 1
    print(f'Total number of clients coonected {conn_clients}')
    print(f'Connected by {client_address} with connection id {conn_clients}')
    
    while True:
        cmd = command_reader.readCommand(client_socket)
        res = command_evaluator.evaluate(cmd)
        print(res)
        client_socket.send(res.encode('utf-8'))
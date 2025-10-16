import socket
from CommandReader import CommandReader
conn_clients = 0
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(('localhost', 7379))
server.listen(5) #max 5 conn will be queued

print('Server is running on port 7379')

command_reader = CommandReader()

while True:
    client_socket, client_address = server.accept()
    conn_clients += 1
    print(f'Connected by {client_address}')
    cmd = command_reader.readCommand(client_socket)
    print(cmd)
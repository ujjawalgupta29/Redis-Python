import socket
import select
import sys
from CommandReader import CommandReader
from CommandEvaluator import CommandEvaluator
from RedisCmd import RedisCmd
from AutoExpire import AutoExpire
from KeyValueStore import KeyValueStore
from Eviction import Eviction
import threading
import signal
from Atomic import Atomic
import time
from ClientStore import ClientStore
from Client import Client

shutdown_event = threading.Event()
EngineStatus_WAITING = 1 << 1
EngineStatus_BUSY = 1 << 2
EngineStatus_SHUTTING_DOWN = 1 << 3
server_status = Atomic(EngineStatus_WAITING)
# Initialize command reader and evaluator
clientStore = ClientStore()
eviction = Eviction()
keyValueStore = KeyValueStore(eviction)
command_reader = CommandReader()
command_evaluator = CommandEvaluator(keyValueStore)
autoExpire = AutoExpire(keyValueStore)

def run_async_tcp_server():
    """Async TCP server using kqueue"""
    print("Starting an asynchronous TCP server on localhost:7379")
    
    max_clients = 20000
    con_clients = 0
    
    # Create kqueue event array
    events = []
    
    # Create server socket
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.setblocking(False)  # Set non-blocking mode
    
    # Bind the IP and port
    server_socket.bind(('localhost', 7379))
    server_socket.listen(max_clients)
    
    # Create kqueue instance 
    kq = select.kqueue()
    
    # Register server socket for read events 
    server_event = select.kevent(
        server_socket.fileno(),
        filter=select.KQ_FILTER_READ,
        flags=select.KQ_EV_ADD | select.KQ_EV_ENABLE
    )
    kq.control([server_event], 0, 0)
    
    print(f'Server is running on port 7379')
    
    try:
        while server_status.get() != EngineStatus_SHUTTING_DOWN:
            #delete expired keys
            autoExpire.cron()
            # Wait for events
            # None means wait indefinitely
            events = kq.control(None, max_clients, None)

            if server_status.get() == EngineStatus_SHUTTING_DOWN:
                break

            if server_status.get() == EngineStatus_WAITING:
                server_status.set(EngineStatus_BUSY)
            
            for event in events:
                # If server socket is ready for IO (new connection)
                if event.ident == server_socket.fileno():
                    try:
                        # Accept incoming new connection
                        client_socket, client_addr = server_socket.accept()
                        client_socket.setblocking(False)  # Set non-blocking
                        
                        # Store client socket in dictionary
                        print(f'Client socket fd: {client_socket.fileno()}')
                        clientStore.addClient(Client(client_socket.fileno(), False, [], client_socket))
                        
                        # Increase concurrent clients count
                        con_clients += 1
                        print(f'Client connected from {client_addr}')
                        print(f'Total number of clients connected: {con_clients}')
                        
                        # Add client to kqueue monitoring
                        client_event = select.kevent(
                            client_socket.fileno(),
                            filter=select.KQ_FILTER_READ,
                            flags=select.KQ_EV_ADD | select.KQ_EV_ENABLE
                        )
                        kq.control([client_event], 0, 0)
                        
                    except socket.error as e:
                        print(f"Error accepting connection: {e}")
                        continue
                        
                else:
                    # Handle client data
                    try:
                        # Get client socket from dictionary
                        if clientStore.getClient(event.ident) is None:
                            print(f"Client {event.ident} not found in client_sockets")
                            continue
                            
                        client = clientStore.getClient(event.ident)
                        client_socket = client.socket
                        
                        # Check if client is still connected
                        try:
                            cmds = command_reader.readCommand(client_socket)
                            if cmds is None:
                                # Client disconnected or no data
                                print(f"Client {event.ident} disconnected or sent empty data")
                                raise ConnectionError("Client disconnected")
                                
                            res = ""
                            for cmd in cmds:
                                res = res + command_evaluator.evaluate(client, cmd)
                            print(f"Response: {res}")
                            # Send response back to client
                            client_socket.send(res.encode('utf-8'))
                            
                        except (ConnectionResetError, ConnectionAbortedError, OSError) as e:
                            print(f"Client {event.ident} disconnected: {e}")
                            raise e
                        
                    except Exception as e:
                        print(f"Error handling client {event.ident}: {e}")
                        # Clean up client
                        try:
                            # Remove from kqueue monitoring
                            kq.control([select.kevent(
                                event.ident,
                                filter=select.KQ_FILTER_READ,
                                flags=select.KQ_EV_DELETE
                            )], 0, 0)
                            
                            # Close and remove client socket
                            if clientStore.getClient(event.ident) is not None:
                                clientStore.getClient(event.ident).socket.close()
                                clientStore.removeClient(event.ident)
                            
                            con_clients -= 1
                            print(f'Client {event.ident} disconnected. Total clients: {con_clients}')
                            
                        except Exception as cleanup_error:
                            print(f"Error during cleanup for client {event.ident}: {cleanup_error}")
                        continue

            server_status.set(EngineStatus_WAITING)
                        
    except KeyboardInterrupt:
        print("\nShutting down server...")
    except Exception as e:
        print(f"Server error: {e}")
    finally:
        # Cleanup
        print("Cleaning up all client connections...")
        for client in clientStore.clients.values():
            try:
                client.socket.close()
                clientStore.removeClient(client)
            except:
                pass

def wait_for_signal():
    shutdown_event.wait()

def signal_handler(signum, frame):
    print(f"Signal {signum} received. Shutting down server...")
    shutdown_event.set()

    while server_status.get() == EngineStatus_BUSY:
        time.sleep(0.1)

    server_status.set(EngineStatus_SHUTTING_DOWN)
    command_evaluator.evaluate(Client(0, False, [], None), RedisCmd("BGREWRITEAOF", []))
    sys.exit(0)

if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    server_thread = threading.Thread(target=run_async_tcp_server, daemon=True)
    server_thread.start()

    signal_thread = threading.Thread(target=wait_for_signal, daemon=True)
    signal_thread.start()

    server_thread.join()
    signal_thread.join()
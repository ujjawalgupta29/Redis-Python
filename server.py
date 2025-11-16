import socket
import select
import sys
from CommandReader import CommandReader
from CommandEvaluator import CommandEvaluator
from RedisCmd import RedisCmd
from AutoExpire import AutoExpire
from KeyValueStore import KeyValueStore
from Eviction import Eviction

def run_async_tcp_server():
    """Async TCP server using kqueue"""
    print("Starting an asynchronous TCP server on localhost:7379")
    
    max_clients = 20000
    con_clients = 0
    
    # Dictionary to store client sockets by file descriptor
    client_sockets = {}
    
    # Create kqueue event array
    events = []
    
    # Create server socket
    server_fd = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_fd.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_fd.setblocking(False)  # Set non-blocking mode
    
    # Bind the IP and port
    server_fd.bind(('localhost', 7379))
    server_fd.listen(max_clients)
    
    # Create kqueue instance 
    kq = select.kqueue()
    
    # Register server socket for read events 
    server_event = select.kevent(
        server_fd.fileno(),
        filter=select.KQ_FILTER_READ,
        flags=select.KQ_EV_ADD | select.KQ_EV_ENABLE
    )
    kq.control([server_event], 0, 0)
    
    # Initialize command reader and evaluator
    eviction = Eviction()
    keyValueStore = KeyValueStore(eviction)
    command_reader = CommandReader()
    command_evaluator = CommandEvaluator(keyValueStore)
    autoExpire = AutoExpire(keyValueStore)
    
    print(f'Server is running on port 7379')
    
    try:
        while True:

            #delete expired keys
            autoExpire.cron()
            # Wait for events
            # None means wait indefinitely
            events = kq.control(None, max_clients, None)
            
            for event in events:
                # If server socket is ready for IO (new connection)
                if event.ident == server_fd.fileno():
                    try:
                        # Accept incoming new connection
                        client_fd, client_addr = server_fd.accept()
                        client_fd.setblocking(False)  # Set non-blocking
                        
                        # Store client socket in dictionary
                        client_sockets[client_fd.fileno()] = client_fd
                        
                        # Increase concurrent clients count
                        con_clients += 1
                        print(f'Client connected from {client_addr}')
                        print(f'Total number of clients connected: {con_clients}')
                        
                        # Add client to kqueue monitoring
                        client_event = select.kevent(
                            client_fd.fileno(),
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
                        if event.ident not in client_sockets:
                            print(f"Client {event.ident} not found in client_sockets")
                            continue
                            
                        client_socket = client_sockets[event.ident]
                        
                        # Check if client is still connected
                        try:
                            cmds = command_reader.readCommand(client_socket)
                            if cmds is None:
                                # Client disconnected or no data
                                print(f"Client {event.ident} disconnected or sent empty data")
                                raise ConnectionError("Client disconnected")
                                
                            res = ""
                            for cmd in cmds:
                                res = res + command_evaluator.evaluate(cmd)
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
                            if event.ident in client_sockets:
                                client_sockets[event.ident].close()
                                del client_sockets[event.ident]
                            
                            con_clients -= 1
                            print(f'Client {event.ident} disconnected. Total clients: {con_clients}')
                            
                        except Exception as cleanup_error:
                            print(f"Error during cleanup for client {event.ident}: {cleanup_error}")
                        continue
                        
    except KeyboardInterrupt:
        print("\nShutting down server...")
    except Exception as e:
        print(f"Server error: {e}")
    finally:
        # Cleanup
        print("Cleaning up all client connections...")
        for fd, client_socket in client_sockets.items():
            try:
                client_socket.close()
            except:
                pass
        
        kq.close()
        server_fd.close()
        print("Server cleanup completed")

if __name__ == "__main__":
    run_async_tcp_server()
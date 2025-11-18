import socket
import threading
import time
import random

def encode(data):
        res = ""
        tokens = data.split(" ")
        for token in tokens:
            res = res + encodeString(token)
        return f"*{len(tokens)}\r\n{res}"


def encodeString(data):
    return f"${len(data)}\r\n{data}\r\n"

def get_random_key_value():
    token = random.randint(0, 5_000_000)
    return f"k{token}", token

def bulkFire(thread_id):
    try:
        conn = socket.create_connection(('localhost', 7379))
    except Exception as e:
        print(f"Error connecting to server: {e}")
        return

    while True:
        time.sleep(0.5)
        key, value = get_random_key_value()
        cmd = f"SET {key} {value}"
        encoded_cmd = encode(cmd)
        conn.sendall(encoded_cmd.encode('utf-8'))

        try:
            response = conn.recv(512)
            if not response:
                print(f"[Thread {thread_id}] Server closed connection")
                return
        except Exception as e:
            print("Read error:", e)
            return

def main():
    threads = []
    for i in range(10):
        thread = threading.Thread(target=bulkFire, args=(i,))
        thread.start()
        threads.append(thread)

    for thread in threads:
        thread.join()

if __name__ == "__main__":
    main()
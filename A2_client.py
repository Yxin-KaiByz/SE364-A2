import argparse
import getpass
import select
import signal
import socket
import ssl
import sys
import threading

from utils import *

SERVER_HOST = 'localhost'

stop_thread = False

def get_and_send(client):
    while not stop_thread:
        prefix = "me: "
        data = sys.stdin.readline().strip()
        if data:
            print("\033[F\033[K"+f"\r{prefix}"+data)
            send(client.sock, data)

class ChatClient():

    def __init__(self, name, port, host=SERVER_HOST):
        self.name = name
        self.connected = False
        self.host = host
        self.port = port

        #Enable client side encryption
        self.context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2, ssl.CERT_NONE)
        self.context.set_ciphers('AES128-SHA')

        # Initial prompt
        self.prompt = f'[{name}@{socket.gethostname()}]> '
        
        # Connect to server at port
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock = self.context.wrap_socket(self.sock, server_hostname=host)
            self.sock.connect((host, self.port))
            print(f'Now connected to chat server@ port {self.port}')
            self.connected = True
            
            # Send my name...
            send(self.sock, 'NAME: ' + self.name)

            threading.Thread(target=get_and_send, args=(self,)).start()

        except socket.error as e:
            print(f'Failed to connect to chat server @ port {self.port}')
            sys.exit(1)

    def cleanup(self):
        """Close the connection and wait for the thread to terminate."""
        self.sock.close()

    def run(self):
        """ Chat client main loop """
        while self.connected:
            try:
                sys.stdout.flush()

                # Wait for input from stdin and socket
                readable, writeable, exceptional = select.select(
                    [self.sock], [], [])

                for sock in readable:
                    if sock == self.sock:
                        data = receive(self.sock)
                        if not data:
                            print('Client shutting down.')
                            self.connected = False
                            break
                        else:
                            sys.stdout.write(data)
                            sys.stdout.flush()

            except KeyboardInterrupt:
                print(" Client interrupted. " "")
                stop_thread = True
                self.cleanup()
                break

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    name = input("Login\nUsername: ")

    parser.add_argument('--port', action="store",
                        dest="port", type=int, required=True)
    given_args = parser.parse_args()

    port = given_args.port

    client = ChatClient(name=name, port=port)
    client.run()

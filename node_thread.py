import threading
import config as c
import socket

def server_client_threading():
    client = threading.Thread(target = send_data, args = (), daemon = True)
    server = threading.Thread(target = server_thread, args = (), daemon = True)

def send_data():
    pass

def server_thread():
    while True:

        bytesAddressPair = s.recvfrom(c.BUFSIZE)
        msg_string, client_address = bytesAddressPair[0].decode(), bytesAddressPair[1]
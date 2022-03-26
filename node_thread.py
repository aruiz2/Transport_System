import threading, socket, sys
import config as c

def send_file_request(peer_info, filename):
    #Set up socket and connection
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_ip = socket.gethostbyname(peer_info["hostname"])
    server_address = (server_ip, peer_info["port"])
    
    #Build request message
    request_msg = "FILE_REQUEST:" + filename
    s.sendto(request_msg.encode(), server_address)
    s.close()

def server_thread(node_info):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_ip = socket.gethostbyname(node_info["hostname"])
    server_address = (server_ip, node_info["port"])
    s.bind(server_address)

    while True:
        bytesAddressPair = s.recvfrom(c.BUFSIZE)
        msg_string, client_address = bytesAddressPair[0].decode(), bytesAddressPair[1]
    
    s.close()
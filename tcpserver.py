import sys
import config as c
from node_thread import *
import json

def main():
    #parse the input conf file
    file = sys.argv[1]
    node_info = None
    with open(file, 'r') as info:
        node_info = json.load(info)

    #Create server socket
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_ip = socket.gethostbyname(node_info["hostname"])
    server_address = (server_ip, node_info["port"])
    s.bind(server_address)
    print("node address: ", [node_info["hostname"], node_info["port"], server_ip])
    
    #Start server thread
    server = threading.Thread(target = server_thread, args = (node_info, s, ), daemon = True)
    server.start()

    while True:
        filename = input()

        if len(filename) != 0:
            c.filename = filename
            peer_info = find_peer_with_file(node_info, filename)
            if peer_info: send_file_request(peer_info, filename, s, server_address)

def find_peer_with_file(node_info, file_required):
    for peer in node_info["peer_info"]:
        for file in peer["content_info"]:
            if file == file_required: return peer
    return None

if __name__ == '__main__':
    main()
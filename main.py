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

    server = threading.Thread(target = server_thread, args = (node_info, ), daemon = True)
    server.start()

    while True:
        command = input()

        if len(command) != 0:
            peer_info = find_peer_with_file(node_info, command)
            client = threading.Thread(target = send_file_request, args = (peer_info, command, ), daemon = True)
            client.start()

def find_peer_with_file(node_info, file_required):
    for peer in node_info["peer_info"]:
        for file in peer["content_info"]:
            if file == file_required: return peer
    return None

if __name__ == '__main__':
    main()
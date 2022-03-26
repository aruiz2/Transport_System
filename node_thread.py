import threading, socket, sys, pickle
import config as c

def send_file_request(peer_info, filename, s, server_address):
    #Set up socket and connection
    server_ip = socket.gethostbyname(peer_info["hostname"])
    client_address = (server_ip, peer_info["port"])
    
    #Build request message
    request_msg = pickle.dumps("FILE_REQUEST:" + filename)

    print(f'sending file request to {client_address} from {server_address}')
    s.sendto(request_msg, client_address)

def server_thread(node_info, s):
    global fileframes
    fileframes = [] #stores all the file frames so we can retrasmit in case of negative ACK

    while True:
        bytesAddressPair = s.recvfrom(c.BUFSIZE)
        if not bytesAddressPair: break
        msg, client_address = pickle.loads(bytesAddressPair[0]), bytesAddressPair[1]
        print(f'received msg {msg} from client {client_address}')

        #Write the data
        if type(msg) == list:
            print(msg)

        elif msg[:12] == "FILE_REQUEST":
            client = threading.Thread(target = send_file, args = (client_address, msg[13:], s,  ), daemon = True)
            client.start()

        #Received Negative ACK
        elif msg[:7] == "NEG_ACK":
            frame_to_resend = int(msg[7])
            resend_frame(frame_to_resend, client_address, s)

    s.close()

#Send file with Selective Repeat AQR
def send_file(client_address, filename, s):
    global fileframes

    print('sending frames to: ', client_address)
    f = open(filename, "rb")
    frame = f.read(c.PACKETSIZE); fileframes.append(frame); frame_num = 0
    #TODO: IMPLEMENT SO THAT IT ONLY READS UNTIL WE REACHED THE END OF WINDOW// UPDATE WINDOW ACCORDINGLY
    while (frame):
        msg = pickle.dumps([frame_num, frame])
        s.sendto(msg, client_address)
        frame = f.read(c.PACKETSIZE); fileframes.append(frame)
        frame_num += 1

#Resends frame when received negative ACK
def resend_frame(frame, client_address, s):
    global fileframes
    s.sendto(fileframes[frame].encode(), client_address)
    
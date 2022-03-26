import threading, socket, sys, pickle
import config as c

def send_file_request(peer_info, filename, s, server_address):
    c.fileframes_received = {} #stores all the file frames so we can retrasmit in case of negative ACK
    print('cleared c.fileframes_received: ', c.fileframes_received)
    #Set up socket and connection
    server_ip = socket.gethostbyname(peer_info["hostname"])
    client_address = (server_ip, peer_info["port"])
    
    #Build request message
    request_msg = pickle.dumps("FILE_REQUEST:" + filename)

    #Create empty file to write data that we receive in the future
    print(filename.split('.'))
    filename_test = filename.split('.')[0] + 'test.' + filename.split('.')[1]
    f = open(filename_test, 'wb') #TODO: FOR SUBMIT CHANGE TO FILENAME
    f.close()

    #Send the request
    print(f'sending file request to {client_address} from {server_address}')
    s.sendto(request_msg, client_address)

def server_thread(node_info, s):

    while True:
        bytesAddressPair = s.recvfrom(c.BUFSIZE)
        if not bytesAddressPair: break
        msg, client_address = pickle.loads(bytesAddressPair[0]), bytesAddressPair[1]
        #print(f'received msg {msg} from client {client_address}')

        #Write the data into array
        if type(msg) == list:
            frame_number = msg[0]
            frame_content = msg[1]
            c.fileframes_received[frame_number] = frame_content

        elif msg == "DONE":
            f = open('imtest.jpeg', 'wb')
            for frame_num in sorted(c.fileframes_received.keys()):
                frame = c.fileframes_received[frame_num]
                f.write(frame)
            f.close()

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
    fileframes_sent = {}

    print('sending frames to: ', client_address)
    f = open(filename, "rb")
    frame = f.read(c.PACKETSIZE); fileframes_sent['0'] = frame; frame_num = 0

    #TODO: IMPLEMENT SO THAT IT ONLY READS UNTIL WE REACHED THE END OF WINDOW// UPDATE WINDOW ACCORDINGLY
    while (frame):
        msg = pickle.dumps([frame_num, frame])
        s.sendto(msg, client_address)

        frame = f.read(c.PACKETSIZE); 
        frame_num += 1
        fileframes_sent[frame_num] = frame
    
    s.sendto(pickle.dumps("DONE"), client_address)

#Resends frame when received negative ACK
def resend_frame(frame, client_address, s):
    s.sendto(fileframes[frame].encode(), client_address)
    
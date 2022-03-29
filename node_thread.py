import threading, socket, sys, pickle, time
import config as c

def send_file_request(peer_info, filename, s, server_address):
    c.fileframes_received = {} #stores all the file frames so we can retrasmit in case of negative ACK

    #Set up socket and connection
    server_ip = socket.gethostbyname(peer_info["hostname"])
    client_address = (server_ip, peer_info["port"])
    
    #Build request message
    request_msg = pickle.dumps("FILE_REQUEST:" + filename)

    #Create empty file to write data that we receive in the future
    filename_test = filename.split('.')[0] + 'test.' + filename.split('.')[1]
    f = open(filename_test, 'wb') #TODO: FOR SUBMIT CHANGE TO FILENAME
    f.close()

    #Send the request
    print(f'sending file request to {client_address} from {server_address}')
    s.sendto(request_msg, client_address)

def server_thread(node_info, s):

    while True:
        #TODO: CHECK THIS IS RIGHT, THIS IS TO CHECK FOR NEGATIVE ACKS ONCE SERVER IS DONE SENDING ALL FRAMES
        if c.received_file_request and c.fileframes_sent_dict:
            send_negative_ack(s, c.client_address, max(list(c.fileframes_sent_dict.keys())))
        
        #Get message received
        bytesAddressPair = s.recvfrom(c.BUFSIZE)
        if not bytesAddressPair: break
        msg, c.client_address = pickle.loads(bytesAddressPair[0]), bytesAddressPair[1]
        
        #Send done signal when received all acks
        if c.received_file_request and c.frames_sent != 0 and len(c.received_acks) == c.frames_sent:
            print(f'length received_acks: {len(c.received_acks)} // frames_sent: {c.frames_sent}\n\n')
            print(f'length fileframes_sent_dict: {len(c.fileframes_sent_dict.keys())}') 
            reset_sender_frame_variables()
            s.sendto(pickle.dumps("DONE"), c.client_address)

        #Received a packet
        if type(msg) == list:
            frame_number = msg[0]
            frame_content = msg[1]
            c.threadLock.acquire()
            c.fileframes_received[frame_number] = frame_content
            c.threadLock.release()

            send_ack(s, frame_number, c.client_address)

        #received acknowledgement
        elif msg[:3] == "ACK":
            frame_ack_num = int(msg[3:])
            c.threadLock.acquire()
            c.received_acks.add(frame_ack_num)
            c.threadLock.release()
        
        elif msg == "DONE":
            f = open('imtest.jpeg', 'wb')
            for frame_num in sorted(c.fileframes_received.keys()):
                frame = c.fileframes_received[frame_num]
                f.write(frame)
            f.close()
            reset_receiver_frame_variables()

        elif msg[:12] == "FILE_REQUEST":
            c.received_file_request = True
            client = threading.Thread(target = send_file, args = (c.client_address, msg[13:], s,  ), daemon = True)
            client.start()

        #Received Negative ACK
        elif msg[:7] == "NEG_ACK":
            frame_to_resend = int(msg[7:])
            resend_frame(frame_to_resend, c.client_address, s)
        
    s.close()

#Send file with Selective Repeat AQR
def send_file(client_address, filename, s):
    c.fileframes_sent_dict = {}
    window_edge = c.WINDOWSIZE

    print('sending frames to: ', client_address)
    f = open(filename, "rb")
    frame = f.read(c.PACKETSIZE); c.fileframes_sent_dict[0] = frame; frame_num = 0
    

    while (frame):
        msg = pickle.dumps([frame_num, frame])
        for _ in range(3):
            s.sendto(msg, client_address)

            update_fileframes_sent_dict(frame_num, frame)
        
        if frame_num < window_edge:
            frame = f.read(c.PACKETSIZE)
            frame_num += 1
        else:
            if len(c.received_acks) >= window_edge:
                frame_num += 1
                window_edge += 1
                frame = f.read(c.PACKETSIZE)
    
    print(f'done sending {c.frames_sent} frames')
    c.frames_sent = frame_num

#Updates fileframes_sent_dict with threadLock
def update_fileframes_sent_dict(frame_num, frame):
    c.threadLock.acquire()
    c.fileframes_sent_dict[frame_num] = frame
    c.threadLock.release()

#Resends frame when received negative ACK
def resend_frame(frame, client_address, s):
    print(f'resending frame:{frame}')
    print(f'c.received_acks: {c.received_acks}')
    print('\n')

    frame = pickle.dumps(c.fileframes_sent_dict[frame])
    s.sendto(frame, client_address)

#Sends acknowledgements that it has receivedd a frame
def send_ack(s, frame_number, client_address):
    frame_ack = pickle.dumps("ACK" + str(frame_number))

    for _ in range(3):
        s.sendto(frame_ack, client_address)

#Sends negative acknowledgements to account for missing frames
def send_negative_ack(s, client_address, frame_number_received):
    for frame_num in range(frame_number_received): #TODO: MIGHT WANT TO EDIT THIS, MIGHT BE INEFFICIENT
        if frame_num not in c.fileframes_sent_dict.keys():
            
            print(f'sending negative ack for frame{frame_num}')
            neg_ack = pickle.dumps("NEG_ACK" + str(frame_num))
            for _ in range(3):
                s.sendto(neg_ack, client_address)

def reset_receiver_frame_variables():
    c.fileframes_received = {}
    c.frames_sent = 0

def reset_sender_frame_variables():
    c.fileframes_sent_dict = {}
    c.received_acks = set()
    c.received_file_request = False
    c.frames_sent = 0
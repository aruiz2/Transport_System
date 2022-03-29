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
        if c.fileframes_received: 
            send_negative_ack(s, c.client_address, max(list(c.fileframes_received.keys())))
        
        bytesAddressPair = s.recvfrom(c.BUFSIZE)
        if not bytesAddressPair: break
        msg, c.client_address = pickle.loads(bytesAddressPair[0]), bytesAddressPair[1]
        #print(f'received msg {msg} from client {client_address}')

        #Send done signal when received all acks
        print(f'len(received_acks): {len(c.received_acks)}\nframes_sent: {c.frames_sent}\nc.received_file_request: {c.received_file_request}\n\n')
        # print(f'fileframes_sent_dict: {sorted(c.fileframes_sent_dict.keys())}')
        
        if c.received_file_request and c.frames_sent != 0 and len(c.received_acks) == c.frames_sent:
            print(f'length received_acks: {len(c.received_acks)} // frames_sent: {c.frames_sent}\n\n')
            print(f'length fileframes_sent_dict: {len(c.fileframes_sent_dict.keys())}') 
            reset_sender_frame_variables()
            s.sendto(pickle.dumps("DONE"), c.client_address)

        #Write the data into array
        if type(msg) == list:
            frame_number = msg[0]
            frame_content = msg[1]
            c.threadLock.acquire()
            c.fileframes_received[frame_number] = frame_content
            c.threadLock.release()

            #print(f'c.fileframes_received: {sorted(c.fileframes_received.keys())}')

            send_ack(s, frame_number, c.client_address)
            send_negative_ack(s, c.client_address, frame_number)

        #received acknowledgement
        elif msg[:3] == "ACK":
            frame_ack_num = int(msg[3:])
            c.threadLock.acquire()
            c.received_acks.add(frame_ack_num)
            c.threadLock.release()
            #print(f'received_acks: {c.received_acks}')
        
        elif msg == "DONE":
            # print(f'length fileframes_received: {len(c.fileframes_received)}')
            # print(f'fileframes_received.keys(): {sorted(c.fileframes_received.keys())}')

            #print(f'received_acks: {c.received_acks}')
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
            #print(f"received NEG ACK{frame_to_resend}")
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
            time.sleep(0.0001)

            update_fileframes_sent_dict(frame_num, frame)
        
        if frame_num < window_edge:
            frame = f.read(c.PACKETSIZE)
            frame_num += 1
        else:
            if len(c.received_acks) >= window_edge:
                frame_num += 1
                window_edge += 1
                frame = f.read(c.PACKETSIZE)

    c.frames_sent = frame_num
    
    #TODO: EDIT SO THAT IT ONLY SENDS DONE WHEN IT HAS RECEIVED ALL ACKS
    # s.sendto(pickle.dumps("DONE"), client_address)

#Updates fileframes_sent_dict with threadLock
def update_fileframes_sent_dict(frame_num, frame):
    c.threadLock.acquire()
    c.fileframes_sent_dict[frame_num] = frame
    #print(f'updating fileframes_sent_dict now {sorted(c.fileframes_sent_dict.keys())}')
    c.threadLock.release()

#Resends frame when received negative ACK
def resend_frame(frame, client_address, s):
    print(f'frame:{frame}, fileframes_sent_dict.keys():{list(c.fileframes_sent_dict.keys())}')
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
        if frame_num not in c.fileframes_received:

            neg_ack = pickle.dumps("NEG_ACK" + str(frame_num))
            for _ in range(3):
                s.sendto(neg_ack, client_address)

def reset_receiver_frame_variables():
    c.fileframes_received = {}
    c.frames_sent = 0

def reset_sender_frame_variables():
    #print("RESETTING SENDER_FRAME_VARIABLES")
    c.fileframes_sent_dict = {}
    c.received_acks = set()
    c.received_file_request = False
    c.frames_sent = 0
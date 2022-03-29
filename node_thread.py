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
        bytesAddressPair = s.recvfrom(c.BUFSIZE)
        if not bytesAddressPair: break
        msg, client_address = pickle.loads(bytesAddressPair[0]), bytesAddressPair[1]
        #print(f'received msg {msg} from client {client_address}')

        #Write the data into array
        if type(msg) == list:
            frame_number = msg[0]
            frame_content = msg[1]
            c.threadLock.acquire()
            c.fileframes_received[frame_number] = frame_content
            c.threadLock.release()

            #print(f'c.fileframes_received: {sorted(c.fileframes_received.keys())}')

            send_ack(s, frame_number, client_address)
            send_negative_ack(s, client_address, frame_number)

        #received acknowledgement
        elif msg[:3] == "ACK":
            frame_ack_num = int(msg[3:])
            c.threadLock.acquire()
            c.received_acks.add(frame_ack_num)
            c.threadLock.release()

        elif msg == "DONE":
            # print(f'length fileframes_received: {len(c.fileframes_received)}')
            # print(f'fileframes_received.keys(): {sorted(c.fileframes_received.keys())}')

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
            frame_to_resend = int(msg[7:])
            #print(f"received NEG ACK{frame_to_resend}")
            resend_frame(frame_to_resend, client_address, s)
        

    s.close()

#Send file with Selective Repeat AQR
def send_file(client_address, filename, s):
    c.fileframes_sent_dict = {}

    print('sending frames to: ', client_address)
    f = open(filename, "rb")
    frame = f.read(c.PACKETSIZE); c.fileframes_sent_dict[0] = frame; frame_num = 0

    #TODO: IMPLEMENT SO THAT IT ONLY READS UNTIL WE REACHED THE END OF WINDOW// UPDATE WINDOW ACCORDINGLY
    while (frame):
        msg = pickle.dumps([frame_num, frame])
        for _ in range(3):
            s.sendto(msg, client_address)
            time.sleep(0.0001)
            
        #update fileframes_sent dictionary
        c.threadLock.acquire()
        c.fileframes_sent_dict[frame_num] = frame
        c.threadLock.release()

        #read the next frame
        frame = f.read(c.PACKETSIZE); 
        frame_num += 1
        #print(f'sending frame{frame_num}')
    
    s.sendto(pickle.dumps("DONE"), client_address)

#Resends frame when received negative ACK
def resend_frame(frame, client_address, s):
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
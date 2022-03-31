import threading, socket, sys, pickle, time
import config as c
from reset import *
from send_signals import *

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

        #server debugging statements    
        if c.received_file_request: 
            check_not_received_acks(s, c.client_address)
            # print(f'length received_acks: {len(c.received_acks)}')
            # print(f'received_acks: {c.received_acks}')
            # print(f'len(received_akcs): {len(c.received_acks)} , frames_sent: {c.frames_sent}')
            # print(f'received_file_request: {c.received_file_request}')
            # print('\n\n')

        #client debugging statements
        if not c.received_file_request:
            pass


        #Send done signal when received all acks
        if c.received_file_request and c.frames_sent != 0 and len(c.received_acks) == c.frames_sent:
            print(f'length received_acks: {len(c.received_acks)} // frames_sent: {c.frames_sent}')
            print(f'length fileframes_sent_dict: {len(c.fileframes_sent_dict.keys())}\n\n') 
            reset_sender_frame_variables()
            
            #TODO: WHAT IF THE DONE SIGNAL IS DROPPED?
            for _ in range(3):
                s.sendto(pickle.dumps("DONE"), c.client_address)
        
        #Checks that we received all frames from the server up to current frame, if not send negative ACK
        if len(c.fileframes_received.keys()) > 0:
            send_negative_ack(s, c.client_address, max(list(c.fileframes_received.keys())))
        
        #Get message received
        bytesAddressPair = s.recvfrom(c.BUFSIZE)
        msg, c.client_address = pickle.loads(bytesAddressPair[0]), bytesAddressPair[1]
        
        #Received a packet
        if type(msg) == list:
            frame_number = msg[0]
            frame_content = msg[1]
            #print(f'received packet frame {frame_number}\n')

            if frame_number not in c.fileframes_received: #TODO: MIGHT BE INEFFICIENT
                c.threadLock.acquire()
                c.fileframes_received[frame_number] = frame_content
                c.threadLock.release()
                send_ack(s, frame_number, c.client_address)

            send_negative_ack(s, c.client_address, frame_number)

        #received acknowledgement
        elif msg[:3] == "ACK":
            frame_ack_num = int(msg[3:])
            c.threadLock.acquire()
            c.received_acks.add(frame_ack_num)
            c.threadLock.release()
        
        elif msg == "DONE" and c.fileframes_received:
            print('\nReceived DONE signal\n')
            print(f'frames received: {len(c.fileframes_received.keys())}')
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
            frame_num = int(msg[7:])
            #print(f'received NEG_ACK for frame{frame_num} and trying to resend')
            frame = c.fileframes_sent_dict[frame_num]['frame']

            resend_frame(frame, c.client_address, s)
        
    s.close()

#Send file with Selective Repeat AQR
def send_file(client_address, filename, s):
    c.fileframes_sent_dict = {}
    window_edge = c.WINDOWSIZE

    print('sending frames to: ', client_address)
    f = open(filename, "rb")
    frame = f.read(c.PACKETSIZE);
    frame_num = 0

    while (frame):
        msg = pickle.dumps([frame_num, frame])
        if frame_num < window_edge:
            #print(f'sending frame{frame_num} @window_edge:{window_edge}')
            for _ in range(3):
                s.sendto(msg, client_address)
            update_fileframes_sent_dict(frame_num, frame)

            frame = f.read(c.PACKETSIZE)
            frame_num += 1

            print(f'length sent frame: {len(c.fileframes_sent_dict.keys())}')
            print(f'length received_acks: {len(c.received_acks)}')
            #print(f'received_acks: {c.received_acks}')
            print('\n\n')
        else:
            if len(c.received_acks) >= window_edge:
                #print(f'sending frame{frame_num} @window_edge:{window_edge} with {len(c.received_acks)} received_acks')
                for _ in range(3):
                    s.sendto(msg, client_address)
                update_fileframes_sent_dict(frame_num, frame)

                frame_num += 1
                window_edge += 1
                frame = f.read(c.PACKETSIZE)
    f.close()
    c.frames_sent = frame_num
    print(f'done sending {c.frames_sent} frames')
    # print(f'received_acks: {sorted(c.received_acks)}')

#Updates fileframes_sent_dict with threadLock
def update_fileframes_sent_dict(frame_num, frame):
    c.threadLock.acquire()
    c.fileframes_sent_dict[frame_num] = {'frame': frame, 'time': time.time() - c.start_time}
    c.threadLock.release()

#Checks if it has not received acks from frames that have been sent after a certain period
def check_not_received_acks(s, client_address):
    for frame_num in c.fileframes_sent_dict.keys():
        curr_time = time.time() - c.start_time
        if curr_time - c.fileframes_sent_dict[frame_num]['time'] >= c.ACK_PERIOD:
            if frame_num not in c.received_acks:
                frame = c.fileframes_sent_dict[frame_num]['frame']
                resend_frame(frame, client_address, s)
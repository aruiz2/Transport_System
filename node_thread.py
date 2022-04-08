import threading, socket, sys, pickle, time, os
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

    #Send the request
    print(f'sending file request to {client_address} from {server_address}')
    s.sendto(request_msg, client_address)
    time.sleep(c.sleep_period)

def server_thread(node_info, s):

    while True:

        #Get message received
        bytesAddressPair = s.recvfrom(c.BUFSIZE)
        try:
            msg, client_address = pickle.loads(bytesAddressPair[0]), bytesAddressPair[1]
        except: pass
        client_port = client_address[1]

         #Send DONE signal when received all acks
        if (client_port in c.received_file_request and 
            client_port in c.frames_sent and c.frames_sent[client_port] != 0):
            if c.received_file_request[client_port] and len(c.received_acks[client_port]) == c.frames_sent[client_port]:
                reset_sender_frame_variables(client_port)
                
                print(f'\nsending DONE signal')
                for _ in range(3):
                    s.sendto(pickle.dumps("DONE"), client_address)
        
        #Received a packet
        if type(msg) == list:
            #print('Received frame, sending ACK!')
            frame_number = msg[0]
            frame_content = msg[1]

            #Handle first frame received
            if client_port not in c.fileframes_received:
                c.fileframes_received[client_port] = {}
            
            #All frames
            if frame_number not in c.fileframes_received[client_port]: #TODO: MIGHT BE INEFFICIENT
                c.threadLock.acquire()
                c.fileframes_received[client_port][frame_number] = frame_content
                c.threadLock.release()
                send_ack(s, frame_number, client_address)

    
        #received acknowledgement
        elif msg[:3] == "ACK":
            frame_ack_num = int(msg[3:])
            print(f'received ACK{frame_ack_num}')
            if client_port not in c.received_acks: 
                c.threadLock.acquire()
                c.received_acks[client_port] = set()
                c.threadLock.release()
            c.received_acks[client_port].add(frame_ack_num)
            #print(f'received ACK!\nnow length received acks is {len(c.received_acks[client_port])}')
        
        elif msg == "DONE" and client_port in c.fileframes_received and c.fileframes_received[client_port]:
            print('\nReceived DONE signal\n')
            f = open(c.filename, 'wb') #FOR SUBMIT

            for frame_num in sorted(c.fileframes_received[client_port]):
                frame = c.fileframes_received[client_port][frame_num]
                f.write(frame)
            f.close()

            reset_receiver_frame_variables(client_port)
            print(f'************************************************\ntime taken to receive & write file: {c.time.time() - c.start_time}\n************************************************\n')

        elif msg[:12] == "FILE_REQUEST":
            c.received_file_request[client_port] = True
            client = threading.Thread(target = send_file, args = (client_address, msg[13:], s,  ), daemon = True)
            client.start()

        #Received Negative ACK
        elif msg[:7] == "NEG_ACK":
            frame_num = int(msg[7:])
            frame = c.fileframes_sent_dict[client_port][frame_num]['frame']
            resend_frame(frame_num, frame, client_address, s)
        
    s.close()

#Send file with Selective Repeat AQR
def send_file(client_address, filename, s):
    client_port = client_address[1]
    c.fileframes_sent_dict[client_port] = {}
    window_edge = c.WINDOWSIZE

    print('sending frames to: ', client_address)
    f = open(filename, "rb")
    frame_num = -1
    msg = []
    exit = False

    while not exit:

        if frame_num < window_edge - 1:
            frame = f.read(c.PACKETSIZE)
            print(f'sending frame{frame_num} @window_edge:{window_edge}\n')
            frame_num += 1
            update_fileframes_sent_dict(frame_num, frame, client_port)

            for _ in range(3):
                msg = pickle.dumps([frame_num, frame])
                s.sendto(msg, client_address)
                time.sleep(c.sleep_period)

        else:
            if client_port in c.received_acks and len(c.received_acks[client_port]) == window_edge:
                frame = f.read(c.PACKETSIZE)

                if not frame:
                    exit = True

                else:
                    frame_num += 1
                    print(f'sending frame{frame_num} @window_edge:{window_edge} with {len(c.received_acks[client_port])} received_acks\n')
                    update_fileframes_sent_dict(frame_num, frame, client_port)

                    if frame_num == 3000: 
                        print(f'frame3000 is \n{frame}')


                    for _ in range(3):
                        msg = pickle.dumps([frame_num, frame])
                        print(f'length of message{frame_num}: {len(msg)}')
                        s.sendto(msg, client_address)
                        time.sleep(c.sleep_period)

                    window_edge += 1
            else:
                #before being over the window edge
                if window_edge == c.WINDOWSIZE:
                    for frame_check_num in range(window_edge):
                        if frame_check_num not in c.received_acks[client_port]:
                            frame_check_content = c.fileframes_sent_dict[client_port][frame_check_num]
                            resend_frame(frame_check_num, frame_check_content, client_address, s)

                #once we are over the window edge
                else:
                    curr_time = time.time() - c.start_time
                    if curr_time - c.fileframes_sent_dict[client_port][frame_num]['time'] >= c.ACK_PERIOD:
                        print(f'resending frame{frame_num} @window_edge:{window_edge} with {len(c.received_acks[client_port])} received_acks\n')
                        resend_frame(frame_num, frame, client_address, s)

    f.close()
    c.frames_sent[client_port] = frame_num + 1 #to include the 0 packet

    print(f'done sending {c.frames_sent[client_port]} frames')

    #SEND DONE SIGNAL IF DONE
    if c.received_file_request[client_port] and c.frames_sent[client_port] != 0 and len(c.received_acks[client_port]) == c.frames_sent[client_port]:
        c.threadLock.acquire()
        reset_sender_frame_variables(client_port)
        c.threadLock.release()
        
        print(f'\nsending DONE signal')
        for _ in range(3):
            s.sendto(pickle.dumps("DONE"), client_address)

    
#Updates fileframes_sent_dict with threadLock
def update_fileframes_sent_dict(frame_num, frame, client_port):
    c.threadLock.acquire()
    c.fileframes_sent_dict[client_port][frame_num] = {'frame': frame, 'time': time.time() - c.start_time}
    c.threadLock.release()
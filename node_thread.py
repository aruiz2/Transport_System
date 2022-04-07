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
        msg, client_address = pickle.loads(bytesAddressPair[0]), bytesAddressPair[1]
        client_port = client_address[1]

        #server debugging statements   
        if client_port in c.received_file_request and c.received_file_request[client_port]:
            try:
                print(f'\n{client_port}, length received_acks: {len(c.received_acks[client_port])}')
                #print(f'length sent frames: {len(c.fileframes_sent_dict.keys())}')
                #print(f'length received_acks: {len(c.received_acks)}')
                # print('\n\n')
            except: pass

        #client debugging statements
        if client_port in c.received_file_request and not c.received_file_request[client_port]:
            pass
            #print(f'length received frames {len(c.fileframes_received)}')

         #Send DONE signal when received all acks
        if (client_port in c.received_file_request and 
            client_port in c.frames_sent and c.frames_sent[client_port] != 0):
            if c.received_file_request[client_port] and len(c.received_acks[client_port]) == c.frames_sent[client_port]:
                # print(f'length received_acks: {len(c.received_acks)} // frames_sent: {c.frames_sent}')
                # print(f'length fileframes_sent_dict: {len(c.fileframes_sent_dict.keys())}\n\n') 
                reset_sender_frame_variables(client_port)
                
                print(f'\nsending DONE signal')
                #TODO: WHAT IF THE DONE SIGNAL IS DROPPED?
                for _ in range(3):
                    s.sendto(pickle.dumps("DONE"), client_address)
        
        #Received a packet
        if type(msg) == list:
            frame_number = msg[0]
            frame_content = msg[1]
            #print(f'received packet frame {frame_number}\n')

            #Handle first frame received
            if client_port not in c.fileframes_received:
                c.fileframes_received[client_port] = {}
            
            #All frames
            if frame_number not in c.fileframes_received[client_port]: #TODO: MIGHT BE INEFFICIENT
                c.threadLock.acquire()
                c.fileframes_received[client_port][frame_number] = frame_content
                c.threadLock.release()
                send_ack(s, frame_number, client_address)

            #send_negative_ack(s, client_address, frame_number)
    
        #received acknowledgement
        elif msg[:3] == "ACK":
            frame_ack_num = int(msg[3:])
            if client_port not in c.received_acks: 
                c.threadLock.acquire()
                c.received_acks[client_port] = set()
                c.threadLock.release()
            c.received_acks[client_port].add(frame_ack_num)
        
        elif msg == "DONE" and client_port in c.fileframes_received and c.fileframes_received[client_port]:
            print('\nReceived DONE signal\n')
            #print(f'frames received: {len(c.fileframes_received.keys())}')
            #TODO: EDIT THIS FOR SUBMIT
            f = open(c.filename, 'wb') #FOR SUBMIT
            #f = open('test' + str(node_info['port']) + '.jpeg', 'wb') #FOR TESTING .JPEG
            #f = open('test' + str(node_info['port']) + '.ogg', 'wb') #FOR TESTING .OGG

            for frame_num in sorted(c.fileframes_received[client_port]):
                frame = c.fileframes_received[client_port][frame_num]
                f.write(frame)
            f.close()
            reset_receiver_frame_variables(client_port)
            print(f'************************************************\ntime taken to receive file: {c.time.time() - c.start_time}************************************************\n')

        elif msg[:12] == "FILE_REQUEST":
            c.received_file_request[client_port] = True
            client = threading.Thread(target = send_file, args = (client_address, msg[13:], s,  ), daemon = True)
            client.start()

        #Received Negative ACK
        elif msg[:7] == "NEG_ACK":
            frame_num = int(msg[7:])
            #print(f'received NEG_ACK for frame{frame_num} and trying to resend')
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
    frame = f.read(c.PACKETSIZE);
    frame_num = -1
    msg = []

    print(f'the size of what we are sending is {os.path.getsize(filename)} bytes')
    # exit(-1)

    while (frame):

        if frame_num < window_edge - 1:
            #print(f'sending frame{frame_num} @window_edge:{window_edge}')
            frame_num += 1
            update_fileframes_sent_dict(frame_num, frame, client_port)
            for _ in range(3):
                msg = pickle.dumps([frame_num, frame])
                s.sendto(msg, client_address)
                time.sleep(c.sleep_period)
            
            frame = f.read(c.PACKETSIZE)

            # print(f'length sent frame: {len(c.fileframes_sent_dict.keys())}')
            # print(f'length received_acks: {len(c.received_acks)}')
            # #print(f'received_acks: {c.received_acks}')
            # print('\n\n')
        else:
            if client_port in c.received_acks and len(c.received_acks[client_port]) == window_edge:
                frame_num += 1
                print(f'sending frame{frame_num} @window_edge:{window_edge} with {len(c.received_acks)} received_acks')
                update_fileframes_sent_dict(frame_num, frame, client_port)
                for _ in range(3):
                    msg = pickle.dumps([frame_num, frame])
                    s.sendto(msg, client_address)
                    time.sleep(c.sleep_period)

                window_edge += 1
                frame = f.read(c.PACKETSIZE)
            else:
                curr_time = time.time() - c.start_time
                if curr_time - c.fileframes_sent_dict[client_port][frame_num]['time'] >= c.ACK_PERIOD:
                    print(f'fileframe sent time: {c.fileframes_sent_dict[frame_num]["time"]} \t time: {curr_time}')
                    print(f'resending frame{frame_num} @window_edge:{window_edge} with {len(c.received_acks[client_port])} received_acks\n')
                    resend_frame(frame_num, frame, client_address, s)

    f.close()
    c.frames_sent[client_port] = frame_num + 1 #to include the 0 packet

    print(f'done sending {c.frames_sent[client_port]} frames')
    print(f'received_acks: {len(sorted(c.received_acks[client_port]))}) , c.frames_sent: {c.frames_sent[client_port]}')

    #SEND DONE SIGNAL IF DONE
    if c.received_file_request[client_port] and c.frames_sent[client_port] != 0 and len(c.received_acks[client_port]) == c.frames_sent[client_port]:
        # print(f'length received_acks: {len(c.received_acks)} // frames_sent: {c.frames_sent}')
        # print(f'length fileframes_sent_dict: {len(c.fileframes_sent_dict.keys())}\n\n') 
        reset_sender_frame_variables(client_port)
        
        print(f'\nsending DONE signal')
        #TODO: WHAT IF THE DONE SIGNAL IS DROPPED?
        for _ in range(3):
            s.sendto(pickle.dumps("DONE"), client_address)

    
#Updates fileframes_sent_dict with threadLock
def update_fileframes_sent_dict(frame_num, frame, client_port):
    c.threadLock.acquire()
    c.fileframes_sent_dict[client_port][frame_num] = {'frame': frame, 'time': time.time() - c.start_time}
    c.threadLock.release()
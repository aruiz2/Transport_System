import pickle
import config as c
import time

#Resends frame when received negative ACK
def resend_frame(frame_num, frame, client_address, s):
    # print(f'c.received_acks: {sorted(c.received_acks)}')
    # print(f'fileframes_sent: {list(sorted(c.fileframes_sent_dict.keys()))}')
    # print('\n')

    #update time sent of frame
    c.threadLock.acquire()
    c.fileframes_sent_dict[frame_num]['time'] = time.time() - c.start_time
    c.threadLock.release()

    #send frame
    for _ in range(3):
        msg = pickle.dumps([frame_num, frame])
        s.sendto(msg, client_address)
    time.sleep(c.sleep_period)

#Sends acknowledgements that it has receivedd a frame
def send_ack(s, frame_number, client_address):
    frame_ack = pickle.dumps("ACK" + str(frame_number))

    for _ in range(3):
        s.sendto(frame_ack, client_address)
        time.sleep(c.sleep_period)

#Sends negative acknowledgements to account for missing frames
def send_negative_ack(s, client_address, frame_number_received):
    for frame_num in range(frame_number_received): #TODO: MIGHT WANT TO EDIT THIS, MIGHT BE INEFFICIENT
        if  frame_num not in c.fileframes_received.keys():
            
            #print(f'sending negACK{frame_num}')
            neg_ack = pickle.dumps("NEG_ACK" + str(frame_num))
            for _ in range(3):
                s.sendto(neg_ack, client_address)
                time.sleep(c.sleep_period)
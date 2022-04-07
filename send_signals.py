import pickle
import config as c
import time

#Resends frame when received negative ACK
def resend_frame(frame_num, frame, client_address, s):
    # print(f'c.received_acks: {sorted(c.received_acks)}')
    # print(f'fileframes_sent: {list(sorted(c.fileframes_sent_dict.keys()))}')
    # print('\n')

    client_port = client_address[1]
    #update time sent of frame
    c.threadLock.acquire()
    c.fileframes_sent_dict[client_port][frame_num]['time'] = time.time() - c.start_time
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
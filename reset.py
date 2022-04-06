import config as c
def reset_receiver_frame_variables():
    c.fileframes_received[client_port] = {}
    c.frames_sent = 0

def reset_sender_frame_variables(client_port):
    c.fileframes_sent_dict[client_port] = {}
    c.received_acks[client_port] = set()
    c.received_file_request[client_port] = False
    c.frames_sent[client_port] = 0
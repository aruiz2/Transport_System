import config as c
def reset_receiver_frame_variables():
    c.fileframes_received = {}
    c.frames_sent = 0

def reset_sender_frame_variables():
    c.fileframes_sent_dict = {}
    c.received_acks = set()
    c.received_file_request = False
    c.frames_sent = 0
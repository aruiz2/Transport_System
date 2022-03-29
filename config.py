import threading

#Constants
threadLock = threading.Lock()
PACKETSIZE = 500
WINDOWSIZE = 400
BUFSIZE = 1024

#Data Structures
fileframes_received = {}
fileframes_sent_dict = {}
received_acks = set()

#Others
received_file_request = False
frames_sent = 0
client_address = None
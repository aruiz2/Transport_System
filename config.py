import threading

#Constants
threadLock = threading.Lock()
PACKETSIZE = 500
WINDOWSIZE = 400
BUFSIZE = 1024

#Data Structures
fileframes_received = {}
received_acks = set()

#Others
frames_sent = 0
received_file_request = False
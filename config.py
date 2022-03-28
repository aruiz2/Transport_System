import threading

#Constants
threadLock = threading.Lock()
PACKETSIZE = 500
WINDOWSIZE = 400
BUFSIZE = 1024

#Data Structures
fileframes_received = {}
received_acks = set()
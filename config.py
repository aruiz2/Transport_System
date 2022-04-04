import threading, time

#Constants
threadLock = threading.Lock()
PACKETSIZE = 900
WINDOWSIZE = 400
BUFSIZE = 1024
ACK_PERIOD = 2
start_time = time.time()

#Data Structures
fileframes_received = {}
fileframes_sent_dict = {}
received_acks = set()

#Others
received_file_request = False
frames_sent = 0
client_address = None
time_ack = 0 #Keeps track of the last time we received an ack
sleep_period = 0.001


'''
----------------------------------------------------------------------
Best case
PACKETSIZE = 900, WINDOWSIZE = 400, ACK_PERIOD = 2 -> 24 seconds (varies aslo got 33 seconds)
----------------------------------------------------------------------

Others
PACKETSIZE = 600     800
TIMETAKEN  = 57s     32s
'''
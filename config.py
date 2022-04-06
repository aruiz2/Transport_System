import threading, time

#Constants
threadLock = threading.Lock()
PACKETSIZE = 1000
WINDOWSIZE = 2
BUFSIZE = 1024
ACK_PERIOD = 2
start_time = time.time()

#Data Structures
fileframes_received = {}
fileframes_sent_dict = {}
received_acks = {}

#Others
received_file_request = dict()
frames_sent = {}
time_ack = 0 #Keeps track of the last time we received an ack
sleep_period = 0.001


'''
----------------------------------------------------------------------
Best case
PACKETSIZE = 1000, WINDOWSIZE = 20, ACK_PERIOD = 2 -> 20 SECONDS
PACKETSIZE = 900, WINDOWSIZE = 400, ACK_PERIOD = 2 -> 24 seconds (varies aslo got 33 seconds)
----------------------------------------------------------------------

Others
PACKETSIZE = 600     800
TIMETAKEN  = 57s     32s
'''
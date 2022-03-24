import sys
from parser import mParser
import config as c
from node_thread import *

def main():
    #parse the input conf file
    file = sys.argv[1]
    p = mParser(file)

    server_client_threading()

if __name__ == '__main__':
    main()
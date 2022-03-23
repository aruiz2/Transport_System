import sys
from parser import mParser

def main():
    file = sys.argv[1]
    p = mParser(file)

if __name__ == '__main__':
    main()
__author__ = 'yinp'

import socket
import select
import threading
import os
import time



class RecvThread (threading.Thread):
    def __init__(self, conn):
        threading.Thread.__init__(self)
        self.__connection = conn
        self.__data = b''

    def run(self):
        global  sending
        if sending == False:
            self.__data = self.__connection.recv(1024)
            print self.__data
            sending = True
            time.sleep(0.5)

class SendThread (threading.Thread):
    def __init__(self, conn):
        threading.Thread.__init__(self)
        self.__connection = conn
        self.__data = b''

    def run(self):
        global sending
        if sending == True:
            self.__data = raw_input("please input: ")
            while True:
                self.__connection.sendall(self.__data)
                sending = False
                time.sleep(0.5)

if __name__ == "__main__":
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
    sock.connect(("127.0.0.1", 9001))
    sock.setblocking(0)

    sendThread = SendThread(sock)
    recvThread = RecvThread(sock)
    sending = True
    sendThread.start()
    recvThread.start()


    sock.close()
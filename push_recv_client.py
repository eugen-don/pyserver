#!/usr/bin/env python
__author__ = 'yinp'

import socket
import select
import threading

# class RecvThread (threading.Thread):
#     def __init__(self, conn):
#         self.__connection = conn
#         self.__data = b''
#
#     def run(self):
#         self.__data = self.__connection.recv(1024)

if __name__ == "__main__":
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
    sock.connect(("127.0.0.1", 9001))

    epoll_unit = select.epoll()
    epoll_unit.register(sock.fileno(), select.EPOLLIN | select.EPOLLOUT)

    events = {}
    connections = {}
    requests = {}
    responses = {}

    connections[sock.fileno()] = sock
    sock.sendall("-")
    while True:
        events = epoll_unit.poll()
        # print "event len: {0}".format(len(events))
        for fd, event in events:
            if event & select.EPOLLIN:
                data = connections[fd].recv(1024)
                requests[fd] = data
                if len(requests[fd]) > 0:
                    print "[client-recv] {0}".format(data)
                    responses[fd] = data
                    epoll_unit.modify(fd, select.EPOLLIN)
                else:
                    continue
            elif event & select.EPOLLHUP:
                connections[fd].close()
                epoll_unit.unregister(fd)

    epoll_unit.close()
    sock.close()
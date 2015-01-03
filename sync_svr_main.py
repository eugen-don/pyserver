#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'yinp'

from sync_server import *
import signal
# from protodesc.snake_pb2 import *
import re
import os

# class PyMyGameServer(PySyncServer):
#     def __init__(self, address_tuple):
#         super(PyMyGameServer, self).__init__(address_tuple)
#         self.count = 0
#
#     def _on_connected(self, conn):
#         self.count += 1
#         logging.info("current connected client count: {0}".format(self.count))
#
#     def _on_error(self, session):
#         self.count -= 1
#         logging.info("current connected client count: {0}".format(self.count))
#
#     def _on_hungup(self, session):
#         self.count -= 1
#         logging.info("current connected client count: {0}".format(self.count))
#
#     def _on_decode(self, buff):
#         obj = SnakeRequestHeaderProtocol()
#         obj.ParseFromString(buff)
#         return obj
#
#     def _on_process(self, session):
#         if session.request_data.cmd == 10001:
#             for fd, c in self._connections.items():
#                 # sync to all client
#                 if fd != c.fileno():
#                     if len(session.request_data.body) > 0:
#                         logging.info("---------->>>> fd={0}, reqbody.len={1}"
#                                      .format(fd, len(session.request_data.body)))
#                         c.sendall(session.request_data.body)
#                         self._set_readable(fd)
#         return None
#
#
#     def _on_encode(self, data):
#         return data.SerializeToString()


class BroadcastServer(PySyncServer):
    def __init__(self, address_tuple):
        super(BroadcastServer, self).__init__(address_tuple)
        self.count = 0

    def _on_connected(self, conn):
        self.count += 1
        logging.info("current connected client count: {0}".format(self.count))

    def _on_error(self, session):
        self.count -= 1
        logging.info("current connected client count: {0}".format(self.count))

    def _on_hungup(self, session):
        self.count -= 1
        logging.info("current connected client count: {0}".format(self.count))

    def _on_process(self, session):
        print "hit here 1", session.request_data, session.response_data
        for fd, c in self._server_connection_pool.items():
            print "hit here 2, fd={0}, c.fd={1}".format(fd, c.fd)
            if len(session.request_data) > 0:
                logging.info("---------->>>> fd={0}, reqbody.len={1}".format(fd, len(session.request_data)))
                c.send(session.request_data)
                self._epoll_unit.modify(fd, select.EPOLLIN)
        return None


class SimpleLogicServer(PySyncServer):
    def __init__(self, address_tuple):
        super(SimpleLogicServer, self).__init__(address_tuple, frametime=10/1000.)

    @show_info
    def _on_process(self, connection):
        logging.info(connection.request_data)
        try:
            # connection.request_data, timeout = re.split("#", connection.request_data)
            # print("part1={0}, part2={1}".format(connection.request_data, timeout))
            #
            # time.sleep(int(timeout) / 1000.)
            connection.response_data = connection.request_data

        except:
            logging.debug(sys.exc_info())

        return connection.response_data


mainsvr = SimpleLogicServer(('', 9000))


def interrupt_handler(signum, frame):
    mainsvr.shutdown()

signal.signal(signal.SIGINT, interrupt_handler)

try:
    mainsvr.run()
except (Exception, KeyboardInterrupt), e:
    # print sys.exc_info()
    pass
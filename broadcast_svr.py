#! /usr/bin/env python
__author__ = 'yinp'

# coding: utf-8

import signal
from pycommu.sync_server import *


class PyBroadcastServer(PySyncServer):
    def __init__(self, addr):
        super(PyBroadcastServer, self).__init__(address_tuple=addr, frametime=10/1000.)

    def _on_process(self, connection):
        # return super(PyBroadcastServer, self)._on_process(connection)
        for fd, c in self.connection_pool.items():
            print "hit here 2, fd={0}, c.fd={1}".format(fd, c.fd)
            if len(connection.request_data) > 0:
                logging.info("---------->>>> fd={0}, reqbody.len={1}".format(fd, len(connection.request_data)))
                # c.send(connection.request_data)
                c.response_data = c.request_data
                self._on_encode(c)
                self._on_response(c)
                self._set_readable(fd)

        return None


mainsvr = PyBroadcastServer(('', 9001))


def interrupt_handler(signum, frame):
    mainsvr.shutdown()

signal.signal(signal.SIGINT, interrupt_handler)

try:
    mainsvr.run()
except (Exception, KeyboardInterrupt), e:
    pass
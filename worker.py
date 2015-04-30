#!/usr/bin/env python
__author__ = 'yinp'

# worker server

from sync_server import PySyncServer
import sys

class Worker (PySyncServer):
    def __init__(self, address_tuple):
        super(Worker, self).__init__(address_tuple, frametime=10/1000.)


if __name__ == "__main__":
    w = Worker(("", int(sys.argv[1])))
    w.run()
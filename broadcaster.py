#!/usr/bin/env python
__author__ = 'yinp'

from broadcast_svr import PyBroadcastServer


class Broadcaster (PyBroadcastServer):
    def __init__(self, addr):
        super(Broadcaster, self).__init__(addr)


if __name__ == "__main__":
    b = Broadcaster(("", 9500))
    b.run()
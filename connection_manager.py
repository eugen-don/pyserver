# -*- coding: utf-8 -*-
__author__ = 'yinp'

import sys
from session import PySession
from session import const
import threading
import errno
from common import *


class PySessionWorkerThread(threading.Thread):
    """
    处理每个连接的工作线程
    """
    def __init__(self, session):
        super(PySessionWorkerThread, self).__init__()
        self._current_session = session

    def run(self):
        if self._current_session.connect_ex() != 0:
            raise RuntimeError("session connect failed, errno={0}".format(errno.errorcode))

        # TODO:
        self._current_session.send()
        self._current_session.recv()
        self._current_session.process()
        self._current_session.close()


class PyConnectionManager(object):
    """
    管理一批量客户端连接对象(PyConnector)，它们将以同步方式与服务器通信
    此类本身可创建PyConnector对象（工厂模式），也可以从外部添加连接对象
    此类管理下的客户端连接对象生命周期是一发一收一处理
    """
    def __init__(self):
        self._sessions = {}
        self._threads = {}

    @show_info
    def create_session(self, ip, port, name="noname", timeout=300,  blocking=False, blen=const.PACKET_LENGTH):
        session = PySession(ip, port, name=name, timeout=timeout, blocking=blocking, blen=blen)
        self.add_session(session)
        return session

    @show_info
    def add_session(self, session):
        self._sessions[session.fd] = session

    # connect op was moved into thread
    @show_info
    def prepare(self):
        try:
            for fd, session in self._sessions.items():
                session.connect()
        except RuntimeError:
            logging.debug(sys.exc_info())

    # TODO: 优化循环体内容
    # TODO: 使用多线程优化
    @show_info
    def startup(self):
        """
        处理所有连接对象
        """
        for fd, session in self._sessions.items():
            session.send()
            session.recv()
            session.process()
            session.close()
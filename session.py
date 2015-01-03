# -*- coding: utf-8 -*-
__author__ = 'yinp'

import sys
import time
import select
import socket
import errno
import math
from common import *

# 常量定义
const = PyConst()
const.PACKET_LENGTH = 2*(1024**2)
const.EVENT_NUM = 1024

const.DISCONNECTED = 0
const.CONNECTED = 1

# noinspection PyBroadException
class PySession(object):
    """
    客户端连接类，封装SOCKET基本操作以及客户端相关的通信数据编解码，以及数据处理逻辑
    """
    def __init__(self, ip, port,
                 name="noname", timeout=300, blocking=False,
                 blen=const.PACKET_LENGTH):
        """

        :param ip:
        :param port:
        :param blocking:
        :return:
        """

        # self._session_mgr = None
        self._server_ip = ip
        self._server_port = port
        self._buffer_len = blen
        self._blocking = blocking
        self._request_buff = b''
        self._response_buff = b''
        self._response_data = None
        self._timeout_processed = False
        self._request_data = None
        self._timeout = timeout         # 网络通信及后端处理时延（不包括连接建立时间）
        self._start_time = time.time()
        self._event_mask = select.EPOLLOUT
        self._sock_obj = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._status = const.DISCONNECTED
        self._name = name
        if len(self._name) == 0 or self._name == "noname":
            self._name = "{0}:{1}".format(ip, port)

    def __del__(self):
        """
        析构方法
        """
        self._sock_obj.close()
        del self._sock_obj

    def __str__(self):
        return "{3}#{0}:{1}${2}".format(self._server_ip, self._server_port, self.__hash__(), self._name)

    @property
    def raw_socket(self):
        return self._sock_obj

    @raw_socket.setter
    def raw_socket(self, v):
        self._sock_obj = v
        self._status = const.CONNECTED

    @property
    def status(self):
        return self._status

    @property
    def starttime(self):
        return self._start_time

    @starttime.setter
    def starttime(self, v):
        self._start_time = v

    @property
    def timeout(self):
        return self._timeout

    @timeout.setter
    def timeout(self, v):
        self._timeout = v

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, v):
        self._name = v

    @property
    def blocking(self):
        return self._blocking

    @blocking.setter
    def blocking(self, b):
        self._blocking = b

    def connectex(self):
        return self._sock_obj.connect_ex((self._server_ip, self._server_port))

    @show_info
    def connect(self):
        """
        连接服务器
        """
        try:
            if self.status == const.DISCONNECTED:
                self._sock_obj.connect((self._server_ip, self._server_port))

                self._sock_obj.setblocking(self._blocking)
                self._status = const.CONNECTED
        except socket.error:
            logging.debug(sys.exc_info())

    def set_readable(self):
        self._event_mask = select.EPOLLIN

    def set_writeable(self):
        self._event_mask = select.EPOLLOUT

    def set_event_mask(self, em):
        self._event_mask = em

    def get_event_mask(self):
        return self._event_mask

    @property
    def fd(self):
        return self._sock_obj.fileno()

    @show_info
    def process(self):
        logging.info('[{0}:{2}]in connector process: {1}'.format(self.fd, self._response_data, time.time()))

    @show_info
    def _on_encode(self):
        """
        _request_data -> _request_buff
        :return:
        """
        # self._request_buff = self._request_data
        return self._request_data

    @show_info
    def _on_decode(self):
        """
        _response_buff -> _response_data
        :return:
        """
        # self._response_data = self._response_buff
        return self._response_buff

    @show_info
    def _on_error(self, code):
        """
        逻辑出错处理, 由应用层决定特定错误的处理方式，是中断还是继续
        :param code:
        :return:
        """
        pass

    @show_info
    def reset_timer(self):
        """
        重置开始时间
        :return:
        """
        self._timeout_processed = False
        self._start_time = time.time()

    @show_info
    def check_timeout(self):
        now = math.floor(time.time() * 1000)
        if math.floor(self._start_time * 1000) + self._timeout < now:
            # 当前SESSION已经超时
            logging.info("timeout - starttime: {0}, timeout={1}, now={2}".format(self._start_time, self._timeout, now))
            return True
        else:
            logging.info("not timeout")
            return False

    @show_info
    def timeout_notify(self):
        """
        执行超时处理
        :return:
        """
        if not self._timeout_processed:
            self._on_timeout()
            self._timeout_processed = True

    @show_info
    def _on_timeout(self):
        """
        超时处理，由派生类实现
        :return:
        """
        logging.info("timeout handler was invoked <--------------------")
        # self._session_mgr.remove_session(self.fd)

    @property
    def request_buffer(self):
        return self._request_buff

    @request_buffer.setter
    def request_buffer(self, bufdata):
        self._request_buff = bufdata

    @property
    def response_buffer(self):
        return self._response_buff

    @response_buffer.setter
    def response_buffer(self, bufdata):
        self._response_buff = bufdata

    @property
    def request_data(self):
        return self._request_data

    @request_data.setter
    def request_data(self, data):
        self._request_data = data

    @property
    def response_data(self):
        return self._response_data

    @response_data.setter
    def response_data(self, data):
        self._response_data = data

    @property
    def remote_ip(self):
        return self._server_ip

    @property
    def remote_port(self):
        return self._server_port

    @property
    def remote_addr(self):
        return self._server_ip, self._server_port

    @show_info
    def send(self, buff=None):
        try:
            if self._status == const.CONNECTED:
                if buff is None:
                    self._request_buff = self._on_encode()
                    logging.info("buff={0}, data={1}".format(self._request_buff, self._request_data))
                    self._sock_obj.sendall(self._request_buff)
                else:
                    self._sock_obj.sendall(buff)
            else:
                raise socket.error("not connected")
        except socket.error:
            logging.debug(sys.exc_info())

    @show_info
    def recv(self):
        try:
            if self._status == const.CONNECTED:
                self._response_buff = self._sock_obj.recv(self._buffer_len)
                self._response_data = self._on_decode()

            else:
                raise socket.error("not connected")
        except socket.error:
            logging.debug(sys.exc_info())
        finally:
            return len(self._response_buff)

    @show_info
    def close(self):
        self._sock_obj.close()
        self._status = const.DISCONNECTED
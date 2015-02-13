#!/usr/bin/env python
# -*- encoding: UTF-8 -*-

from session import *
import logging


class PyServerConnection(object):
    def __init__(self, connection, length=const.PACKET_LENGTH):
        self.__request_buffer = b''
        self.__response_buffer = b''
        self.__request_data = b''
        self.__response_data = b''
        self.__raw_connection = connection
        self.__fd = connection.fileno()
        self.__packet_length = length

    @property
    def connection(self):
        return self.__raw_connection

    @property
    def fd(self):
        return self.__raw_connection.fileno()

    @property
    def request_data(self):
        return self.__request_data

    @request_data.setter
    def request_data(self, v):
        self.__request_data = v

    @property
    def response_data(self):
        return self.__response_data

    @response_data.setter
    def response_data(self, v):
        self.__response_data = v

    @property
    def request_buffer(self):
        return self.__request_buffer

    @request_buffer.setter
    def request_buffer(self, v):
        self.__request_buffer = v

    @property
    def response_buffer(self):
        return self.__response_buffer

    @response_buffer.setter
    def response_buffer(self, v):
        self.__response_buffer = v

    def send(self):
        self.__raw_connection.sendall(self.__response_buffer)

    def recv(self):
        self.__request_buffer = self.__raw_connection.recv(self.__packet_length)

class PySyncServer(object):
    """
    同步服务器基类，子类可实现自定义的编解码逻辑以及连接断开、出错等处理逻辑
    基类的编解码都是作透传
    """
    def __init__(self, address_tuple, frametime=-1, blen=const.PACKET_LENGTH):
        # Private Instance Members #
        self._server_ip, self._server_port = address_tuple
        # self._connections = {}    # obsolete
        self._server_connection_pool = {}
        self._request_list = {}
        self._response_list = {}
        self._events = {}
        self._epoll_unit = select.epoll()
        self._buffer_len = blen
        self._frame_time = frametime
        self.__shutdown = False

        self._server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server_sock.setblocking(0)
        self._server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        # 屏蔽信号Ctrl+C操作
        # signal.signal(signal.SIGINT, signal.SIG_IGN)

    def __del__(self):
        self.shutdown()

    def shutdown(self):
        if not self.__shutdown:
            logging.info("Server is shuting down...")
            self._epoll_unit.unregister(self._server_sock.fileno())

            self._server_sock.close()
            self._epoll_unit.close()

            if "_PySyncServer_server_connection_pool" in vars(self):
                del self._server_connection_pool

            if "_PySyncServer_events" in vars(self):
                del self._events

            self.__shutdown = True
            logging.info("Server was stopped...")

    def _prepare(self):
        pass

    @property
    def connection_pool(self):
        return self._server_connection_pool

    @show_info
    def _on_connected(self, connection):
        """
        连接建立时的逻辑处理，如连接数统计等
        """
        pass

    @show_info
    def _on_process(self, connection):
        connection.response_data = connection.request_data
        return connection.response_data

    @show_info
    def _on_error(self, connection):
        pass

    @show_info
    def _on_hungup(self, connection):
        pass

    @show_info
    def _cleanup_peer_connect(self, fd):
        logging.info("clean up peer connect, fd={0}".format(fd))
        self._epoll_unit.unregister(fd)
        self._server_connection_pool[fd].connection.close()
        del self._server_connection_pool[fd]

    @show_info
    def _on_response(self, connection):
        # logging.info("{0} bytes were send back to client".format(len(self._response_list[conn.fileno()])))
        if len(connection.response_buffer) > 0:
            connection.connection.sendall(connection.response_buffer)

    @show_info
    def _on_encode(self, connection):
        """
        object data -> bytes buffer data
        """
        connection.response_buffer = connection.response_data
        return connection.response_buffer

    @show_info
    def _on_decode(self, connection):
        """
        bytes buffer data -> object data
        """
        connection.request_data = connection.request_buffer

    def _set_readable(self, fd):
        self._epoll_unit.modify(fd, select.EPOLLIN)

    def _set_writeable(self, fd):
        self._epoll_unit.modify(fd, select.EPOLLOUT)

    def _check_packet(self, connection):
        pass

    @show_info
    def run(self):
        """
        运行服务器事件循环，处理 IO事件
        """
        self._server_sock.bind((self._server_ip, self._server_port))
        self._server_sock.listen(32)
        self._epoll_unit.register(self._server_sock.fileno(), select.EPOLLOUT | select.EPOLLIN)

        logging.info("Server Started @ {0}:{1}, Listen Sock is {2}...".format(self._server_ip, self._server_port, self._server_sock.fileno()))
        self._prepare()

        while True:
            try:
                self._events = self._epoll_unit.poll(timeout=self._frame_time)
                # logging.info("received events len:{0}".format(len(self._events)))
                for fd, event in self._events:
                    if fd == self._server_sock.fileno():
                        # Process a new coming connection
                        connection, address = self._server_sock.accept()
                        connection.setblocking(0)

                        self._epoll_unit.register(connection.fileno())
                        self._epoll_unit.modify(connection.fileno(), select.EPOLLIN)

                        self._server_connection_pool[connection.fileno()] = PyServerConnection(connection)
                        self._on_connected(self._server_connection_pool[connection.fileno()])

                    else:
                        # Process connected fd IO events
                        if event & select.EPOLLIN:
                            self._server_connection_pool[fd].recv()

                            if len(self._server_connection_pool[fd].request_buffer) <= 0:
                                # 客户端数据发送完毕或已经关闭连接(接收到的数据长度为0),服务端要将对应的连接和FD关闭.
                                logging.info("client side has already closed the "
                                             "connection or data send completed, fd={0}".format(fd))

                                self._on_hungup(self._server_connection_pool[fd])
                                self._cleanup_peer_connect(fd)

                            else:
                                # ----------------------------- Process Read IO (recv) ------------------------------- #
                                self._check_packet(self._server_connection_pool[fd])
                                self._on_decode(self._server_connection_pool[fd])

                                # TODO: 尝试使用greenlet将process方法包装成微线程（协程） 运行
                                if self._on_process(self._server_connection_pool[fd]):
                                    self._set_writeable(fd)

                        elif event & select.EPOLLOUT:
                            # ----------------------------- Process Write IO (send) -------------------------------- #
                            self._on_encode(self._server_connection_pool[fd])
                            self._on_response(self._server_connection_pool[fd])
                            self._set_readable(fd)

                        elif event & select.EPOLLHUP:
                            # closed by peer event
                            logging.info("[{0}]close connection from client.".format(fd))
                            self._on_hungup(self._server_connection_pool[fd])
                            self._cleanup_peer_connect(fd)

                        elif event & select.EPOLLERR:
                            self._on_error(self._server_connection_pool[fd])
                            self._cleanup_peer_connect(fd)

            except socket.error:
                self._on_error(self._server_connection_pool[fd])
                self._cleanup_peer_connect(fd)
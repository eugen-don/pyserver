# -*- coding: utf-8 -*-
__author__ = 'yinp'

import sys
from session import const
from async_manager import PyAsyncManager
from sync_server import PySyncServer
from session import PySession
from common import *


# TODO: 实现Session的配置化
#  过载保护
class PyAsyncServer(PySyncServer):
    """
    基于EPOLL接口的异步服务器基类
    """
    def __init__(self, address_tuple, blen=const.PACKET_LENGTH):
        super(PyAsyncServer, self).__init__(address_tuple, blen)
        self._session_conf = {}
        self._session_mgr = PyAsyncManager()

    def __del__(self):
        if "_PyAsyncServer_session_mgr" in vars(self):
            del self._session_mgr

    def add_session_config(self, ip, port, name, timeout=300, blocking=False, blen=const.PACKET_LENGTH):
        """
        告诉SVR需要连接哪些SESSION
        :param ip:
        :param port:
        :param name:
        :param timeout:
        :param blocking:
        :param blen:
        :return:
        """
        session = PySession(ip, port, name=name, timeout=timeout, blocking=blocking, blen=blen)
        self._session_mgr.add_session(session)
        self._session_conf[session.fd] = session

    # Must be implemented by subclass
    @show_info
    def _before_async_commu(self, connection):
        """
        由子类实现的逻辑，可以在向后端发起异步请求之前进行对请求对象和回包对象进行操作
        :param request:
        :param response:
        :return:
        """
        connection.response_data = connection.request_data
        return connection.response_data

    @show_info
    def _after_async_commu(self, connection):
        """
        由子类实现的逻辑，可以在向后端发起异步请求之后进行对请求对象和回包对象进行操作
        :param request:
        :param response:
        :return:
        """
        connection.response_data = connection.response_data
        return connection.response_data

    @show_info
    def _build_response(self, connection):
        """
        由子类实现具体逻辑
        此方法用于构造服务器到前端客户端的回包数据，其数据的构造来源于各个后端服务器的返回
        :return: 返回到前端的回包数据对象
        """
        data = ""
        for name, sess in self._session_mgr.session_pool.items():
            data += "{0}->{1}\n".format(name, sess.response_data)
        connection.response_data = data
        return data

    @show_info
    def _prepare(self):
         # 发起对所有后端服务的网络连接
        self._session_mgr.prepare()
        logging.info("after connect all the backend server, confitems:{0}".format(len(self._session_conf)))

    @show_info
    def _async_invoke(self, connection):
        """
        发起对各个后端服务的异步请求
        :param request:
        :return:
        """
        try:
            # 为每个连接器准备请求数据
            for name, sess in self._session_mgr.session_pool.items():
                sess.request_data = connection.request_data

            logging.info("after set request data for backend activities")

            # 异步等待所有后端服务的返回
            self._session_mgr.process()
        except RuntimeError:
            logging.debug(sys.exc_info())
            raise

    @show_info
    def _on_process(self, connection):
        try:
            # 异步调用前处理逻辑，可以进行一些本地计算
            self._before_async_commu(connection)

            # 异步调用
            self._async_invoke(connection)

            # 构造异步调用返回的结果，得到回包结构
            self._build_response(connection)

            #  异步调用后处理逻辑，可以进行一些本地计算
            self._after_async_commu(connection)

            return connection.response_data

        except Exception:
            logging.debug(sys.exc_info())
            raise


class PyServerConfigAdapter(object):
    """
    读取配置，根据配置内容启动对应的服务器
    """
    def __init__(self, conf="server_config.xml"):
        self.__config_file = conf

    def __prepare(self):
        """
        解析配置文件
        :return:
        """
        pass

    def startup(self):
        pass
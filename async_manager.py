# -*- coding: utf-8 -*-
__author__ = 'yinp'

import sys
import select
from session import PySession
from session import const
import time
import socket
import math
from common import *


class PyAsyncTimerObject(object):
    """
    定时器对象
    """
    def __init__(self, session, timeout=300):
        """

        :param session:
        :param timeout:
        :return:
        '"""
        self.__start_time = math.floor(time.time() * 1000)     # 转换为毫秒单位
        self.__session = session
        self.__timeout_stamp = self.__start_time + timeout          # 初始化时计算到期时间

    @property
    def timeout_stamp(self):
        return self.__timeout_stamp

    @property
    def session(self):
        return self.__session

    @property
    def start_time(self):
        return self.__start_time

    def timeout_notify(self):
        self.__session.timeout_notify()


class PyAsyncTimerUnit(object):
    """
    定时器单元，用于管理定时器对象, 在超时的时候调用定时器对象的处理函数
    """
    def __init__(self, reso=30):
        self.__resolution = reso    # 计时器单元的解析度
        self.__timer_object_pool = {}

    def add_timer_object(self, sess, timeout):
        """
        添加会话对象到定时器集合，接受定时器单元的管理
        定时器单元按一定的时间解析度将定时器对象管理在集合里
        """
        print "add {0} into the timer pool".format(sess.name)
        timeobj = PyAsyncTimerObject(sess, timeout)
        key = math.floor(timeobj.timeout_stamp / self.__resolution)
        if not key in self.__timer_object_pool:
            self.__timer_object_pool[key] = {}  # 初始化定时器对象列表

        if not sess.fd in self.__timer_object_pool[key]:
            self.__timer_object_pool[key][sess.fd] = sess

    def remove_timer(self, fd):
        pass


    def timer_check(self):
        """
        定时器事件检查，触发定时器对象的到期处理
        """
        now = time.time() * 1000
        key = math.floor(now / self.__resolution)
        for k, v in self.__timer_object_pool.items():
            if k <= key:
                # 执行超时处理
                [sess.timeout_notify() for fd, sess in self.__timer_object_pool[k].items()]
                # 执行完毕后删掉超时列表
                del self.__timer_object_pool[k]


class PyAsyncManager(object):
    """
    管理一批客户端连接对象(PySession)，它们将以异步方式与服务器通信
    此类本身可创建PySession对象（工厂模式），也可以从外部添加连接对象
    此类管理下的客户端连接对象生命周期是一发一收一处理

    evnum: 单次触发最大IO事件个数
    frametime: EPOLL周期
    max_backend: 最大后端连接数量（过载保护）
    """
    def __init__(self, evnum=const.EVENT_NUM, frametime=-1, max_backend=100, onceshot=True):
        """
        Construct Method
        :return:
        """
        self._epoll_unit = select.epoll()
        self._session_pool = {}
        self._events = {}
        self._onceshot = onceshot
        self._max_event_num = evnum
        self._result_packet_data = b''
        self._total_connection_count = 0
        self._frame_time = frametime
        self._max_backend_connections = max_backend

    def __del__(self):
        """
        Destroy Method
        :return:
        """
        self._epoll_unit.close()

        if "_PyAsyncManager_session_pool" in vars(self):
            del self._session_pool

        if "_PyAsyncManager_events" in vars(self):
            del self._events

    def shutdown(self):
        self._epoll_unit.close()

    @property
    def frame_time(self):
        return self._frame_time

    @property
    def max_backend_count(self):
        return self._max_backend_connections

    @property
    def session_pool(self):
        return self._session_pool

    def get_session_by_name(self, v):
        return filter(lambda val: val.name == v, self._session_pool.values())

    @show_info
    def add_session(self, sess):
        if not sess.fd in self._session_pool.keys():
            self._session_pool[sess.fd] = sess
            self._epoll_unit.register(sess.fd, select.EPOLLET | select.EPOLLOUT)
        else:
            self._session_pool[sess.fd].set_writeable()
            self._epoll_unit.modify(sess.fd, select.EPOLLET | select.EPOLLOUT)
        # self._timer_unit.add_timer_object(sess, sess.timeout)
        # sess.sessionMgr = self          # 将会话对象与会话管理器关联, 从会话对象内部可以知道当前属于哪个会话管理器
        # self.register_session(sess)       # 添加的时候不用注册，异步框架会在每次向后端发请求之前进行注册

    def _update_session_pool(self):
        # async_manager的角色是主动的客户端，所以应该首先发起写IO
        for fd, sess in self._session_pool.items():
            self.add_session(sess)

    def _set_readable(self, fd):
        if fd in self._session_pool.keys():
            self._session_pool[fd].set_readable()
            self._epoll_unit.modify(fd, select.EPOLLIN)

    def _set_writeable(self, fd):
        if fd in self._session_pool.keys():
            self._session_pool[fd].set_writeable()
            self._epoll_unit.modify(fd, select.EPOLLOUT)

    @show_info
    def create_session(self, ip, port, name="noname", timeout=300, blocking=False, blen=const.PACKET_LENGTH):
        """

        :param ip:
        :param port:
        :param blocking: default is False
        :return:
        """
        sess = PySession(ip, port, name=name, timeout=timeout, blocking=blocking, blen=blen)
        self.add_session(sess)
        return sess

    @show_info
    def remove_session(self, fd):
        """
        从会话池中移除会话
        :param fd:
        :return:
        """
        self._epoll_unit.unregister(fd)
        del self._session_pool[fd]

    @show_info
    def prepare(self):
        try:
            for fd, session in self._session_pool.items():
                session.connect()
        except socket.error:
            logging.debug(sys.exc_info())
        finally:
            pass

    @show_info
    def _wait(self, timeout=-1):
        self._events = self._epoll_unit.poll(timeout)
        return len(self._events)

    @show_info
    def _on_hungup(self, fd):
        self._epoll_unit.unregister(fd)        # 单个后端连接处理完成后将对应后端服务的FD移出，后续每次向后端发起异步请求时都会再次向EPOLL中注册FD
        # self._session_pool[fd].close()        # 去掉这句的注释会导致第二次请求失败（异常），不去掉注释执行正常，需要找下原因
        self._total_connection_count -= 1   # 减少与后端的连接数，但是不能del掉_connections中的项

    @show_info
    def _on_overload(self):
        """
        过程保护方法, 当与后端的连接数或机器负载达到一定阈值时调用
        :return:
        """
        pass

    @show_info
    def timerout_check(self):
        """
        检查所有SESSION是否过期
        :return:
        """
        for fd, session in self._session_pool.items():
            # 如果超时则挂掉与后端的连接
            if session.check_timeout():
                session.timeout_notify()
                # self._on_hungup(fd)

    @show_info
    def process(self):
        self.__loop()

    @show_info
    def __loop(self):
        try:
            self._update_session_pool()

            self._total_connection_count = len(self._session_pool)
            logging.info("current total conntion of backend: {0}".format(self._total_connection_count))

            # 过载保护方法 － 交由业务侧决定如何进行过载保护
            if self._total_connection_count > self._max_backend_connections:
                logging.debug("overload flow was triggered, current connection num: {0}"
                              .format(self._total_connection_count))
                self._on_overload()

            # 如果没有到后端的连接，则直接返回什么都不用做
            if self._total_connection_count <= 0:
                return

            while True:
                self._wait(self._frame_time)
                logging.debug("in coming events:{0}".format(len(self._events)))
                for fd, event in self._events:
                    if event & select.EPOLLIN:
                        self._session_pool[fd].recv()

                        logging.info("backend server response: len={0}".format(len(self._session_pool[fd].response_data)))

                        if len(self._session_pool[fd].response_data) > 0:
                            # IO事件处理完成后检查超时事件
                            if self._session_pool[fd].check_timeout():
                                self._session_pool[fd].timeout_notify()     # 走会话的超时处理逻辑
                            else:
                                self._session_pool[fd].process()   # Biz logic in connector

                        if self._onceshot:
                            # self._on_hungup(fd)
                            self._total_connection_count -= 1
                        else:
                            self._set_writeable(fd)

                    elif event & select.EPOLLOUT:
                        if fd in self._session_pool.keys():
                            if self._session_pool[fd].request_data:
                                self._session_pool[fd].send()
                                self._session_pool[fd].reset_timer()   # 发送数据前重置定时器

                            self._set_readable(fd)

                    elif event & select.EPOLLHUP or event & select.EPOLLERR:
                        # connection was closed by peer
                        logging.info("socket failed or hup, fd={0}".format(fd))
                        self._on_hungup(fd)

                if self._onceshot and self._total_connection_count <= 0:
                    break

                self.timerout_check()   # 每处理一批IO事件执行一次超时检查

        except Exception:
            logging.debug("hit here: {0}".format(sys.exc_info()))
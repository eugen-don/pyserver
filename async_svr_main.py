#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'yinp'

import signal
from async_server import PyAsyncServer

if __name__ == "__main__":
    svr = PyAsyncServer(("localhost", 9100))

    # ISSUE: 当前异步SVR与后端服务是短连接,前端的请求处理一次后SOCKET就CLOSE掉了
    svr.add_session_config(name="backendsvr1", ip="localhost", port=9000)

    svr.run()

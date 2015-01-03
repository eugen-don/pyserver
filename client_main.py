#!/usr/bin/env python
# -*- coding: UTF-8 -*-

from connection_manager import PyConnectionManager
# from cslab import PySyncConnectionManager

# TODO: 同步客户端
if __name__ == '__main__':
    mgr = PyConnectionManager()
    conn = mgr.create_session("localhost", 9000, "client", 300, True)
    conn.request_data = "async server with backend server test"
    mgr.prepare()
    mgr.startup()

    # mgr = PySyncConnectionManager()
    # conn = mgr.create_connector("localhost", 9004, "client", False, True)
    # conn.requestData = "async server with backend server test"
    # mgr.prepare()
    # mgr.loop()

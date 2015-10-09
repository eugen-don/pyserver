#!/usr/bin/env python
__author__ = 'yinp'

# async proxy server

from async_server import PyAsyncServer


if __name__ == "__main__" :
    svr = PyAsyncServer(("", 9100))
    svr.add_session_config(name="login_check_svr", ip="localhost", port=9000)
    svr.add_session_config(name="game_logic_svr", ip="localhost", port=9001)
    # svr.add_session_config(name="backendsvr1", ip="localhost", port=9002)
    svr.run()
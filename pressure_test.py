__author__ = 'yinp'

from common import *

# def timecost(func):
#     def wrapper(*args, **kwargs):
#         start = time.clock()
#         func(*args, **kwargs)
#         end = time.clock()
#         print "used: ", end - start
#     return wrapper

# class TestConnector(threading.Thread):
#     def __init__(self, data):
#         threading.Thread.__init__(self)
#         self.__data = data
#
#     def run(self):
#         client = cslab.PyConnector("localhost", 9000, True)
#         client.set_request_data(self.__data)
#         client.connect()
#         client.send()
#         client.recv()
#         client.close()
#
#
# def startup():
#     t = TestConnector(s)
#     t.start()
#     t.join()
#
#
# def startup2():
#     # for i in range(10):
#     client = cslab.PyConnector("localhost", 9000, True)
#     client.set_request_data(s)
#     client.connect()
#     client.send()
#     client.recv()
#     client.close()

@show_info
def commonmethod():
    print "test common method"


@show_info
class DecorationTest(object):
    def __init__(self):
        pass

    @show_info
    def testfunc1(self):
        print "in class method for wrapper"

    @show_info
    def testfunc2(self, arg1, arg2):
        print arg1, arg2

    @show_info
    def testfunc3(self, arg1=1, arg2=3):
        print arg1, arg2

if __name__ == "__main__":
    # print sys.argv[1]
    # s = ""
    # for i in range(512):
    #     s += "1"
    # t1 = Timer("startup2()", "from __main__ import startup2")
    # print t1.timeit(1000)

    dt = DecorationTest()

    dt.testfunc1()

    dt.testfunc2(22, 42)

    dt.testfunc3()

    commonmethod()
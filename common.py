# -*- coding: utf-8 -*-
__author__ = 'yinp'

import logging


logging.basicConfig(
    format='[%(process)d][L%(lineno)d@%(funcName)s$%(filename)s][%(asctime)s] %(message)s',
    level=logging.INFO)


class ConstError(Exception):
    """
    常量定义异常类
    """
    pass


class PyConst(object):
    """
    常量模拟类
    """
    def __setattr__(self, key, value):
        if key in self.__dict__:
            raise ConstError
        else:
            self.__dict__[key] = value


def show_info(func):
    """
    用于显示函数名称的装饰器
    :param func:
    :return:
    """
    def show_info_wrapper(*argv, **kwargs):
        logging.info("--------> [{0}] <---------".format(func.__name__))
        return func(*argv, **kwargs)

    return show_info_wrapper
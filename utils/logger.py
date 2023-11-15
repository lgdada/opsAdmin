#!/usr/bin/python3
# -*- coding: UTF-8 -*-
import sys
import os
import time
import traceback

sys.path.append(os.path.dirname(__file__))
from getSettings import setting

config = setting.config
debug = config.getboolean('global', 'debug')

def get_time():
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())

class logger(object):
    STYLE = {
        'fore': {
            'black': 30, 'red': 31, 'green': 32, 'yellow': 33,
            'blue': 34, 'purple': 35, 'cyan': 36, 'white': 37,
        },
        'back': {
            'black': 40, 'red': 41, 'green': 42, 'yellow': 43,
            'blue': 44, 'purple': 45, 'cyan': 46, 'white': 47,
        },
        'mode': {
            'bold': 1, 'underline': 4, 'blink': 5, 'invert': 7,
        },
        'default': {
            'end': 0,
        }
    }
    def get_frame(self):
        currentframe = sys._getframe(2)
        return currentframe

    def output_msg(self, msg):
        print(msg)

    def use_style(self, string, mode='', fore='', back=''):
        mode = '%s' % self.STYLE['mode'][mode] if self.STYLE['mode'].get(mode) else ''
        fore = '%s' % self.STYLE['fore'][fore] if self.STYLE['fore'].get(fore) else ''
        back = '%s' % self.STYLE['back'][back] if self.STYLE['back'].get(back) else ''
        style = ';'.join([s for s in [mode, fore, back] if s])
        style = '\033[%sm' % style if style else ''
        end = '\033[%sm' % self.STYLE['default']['end'] if style else ''
        return '%s%s%s' % (style, string, end)

    @staticmethod
    def info(message):
        logger().output_msg(logger().use_style("%s [INFO]: %s" % (get_time(), message),fore='green' ))

    @staticmethod
    def error(message):
        traceback.format_exc()
        currentframe = logger().get_frame()
        logger().output_msg(logger().use_style("%s [ERROR] [%s:%s]: %s" % (get_time(), currentframe.f_code.co_filename,
                                                                        currentframe.f_code.co_firstlineno,
                                                                        message), fore='red'))

    @staticmethod
    def warn(message):
        currentframe = logger().get_frame()
        logger().output_msg(logger().use_style("%s [WARN] [%s:%s]: %s" % (get_time(), currentframe.f_code.co_filename,
                                                                         currentframe.f_code.co_firstlineno,
                                                                          message), fore='yellow'))

    @staticmethod
    def debug(message):
        if debug:
            currentframe = logger().get_frame()
            print(logger().use_style("%s [DEBUG] [%s:%s]: %s" % (get_time(), currentframe.f_code.co_filename,
                                                        currentframe.f_code.co_firstlineno, message), fore='white'))


if __name__ == '__main__':
    logger.debug("dddd")
    logger.warn("dddd")
    logger.info("dddd")
    logger.error("dddd")

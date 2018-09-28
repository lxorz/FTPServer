# -*- coding:utf-8 -*-

import optparse
from core.ftp_server import FTPHandler
import socketserver
from conf import settings


class ArvgHandler(object):
    def __init__(self):
        self.parser = optparse.OptionParser()
        (options, args) = self.parser.parse_args()
        self.verify_args(options, args)

    def verify_args(self, options, args):
        if hasattr(self,args[0]):
            func = getattr(self, args[0])
            func()
        else:
            self.parser.print_help()

    def start(self):
        print('-----start server-----')
        server = socketserver.ThreadingTCPServer((settings.HOST, settings.PORT),FTPHandler)

        server.serve_forever()

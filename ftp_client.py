# -*- coding:utf-8 -*-

import socket
import os
import sys
import optparse
import json
import hashlib

STATUS_CODE = {
250: "Invalid cmd format, e.g:{'action':'get','filename':'test.py','size':344}",
251: "Invalid cmd",
252: "Invalid auth data",
253: "Wrong username or password",
254: "Passed authentication",
255: "filename doesn't provided",
256: "File doesn't exist on server",
257: "ready to send file",
}


class FTPClient(object):
    def __init__(self):
        parser = optparse.OptionParser()
        parser.add_option("-s","--server",dest="server",help="ftp server ip_addr")
        parser.add_option("-P","--port",type="int",dest="port",help="ftp server port")
        parser.add_option("-u","--username",dest="username",help="username")
        parser.add_option("-p","--password",dest="password",help="password")

        self.options,self.args = parser.parse_args()
        self.verify_args(self.options,self.args)
        self.make_connection()

    def make_connection(self):
        self.sock = socket.socket()
        self.sock.connect((self.options.server,self.options.port))

    def verify_args(self,options,args):
        if options.username is not None and options.password is not None:
            pass
        elif options.username is None and options.password is None:
            pass
        else:
            exit("Error:username and password must be provided together..")

        if options.server and options.port:
            if options.port>0 and options.port<65535:
                return True
            else:
                exit("Error:host port must in 0-65535")

    def authenticate(self):
        if self.options.username:
            print(self.options.username,self.options.password)
            return self.get_auth_result(self.options.username,self.options.password)
        else:
            retry_count = 0
            while retry_count < 3:
                username = input("username:").strip()
                password = input("password:").strip()
                return self.get_auth_result(username,password)

    def get_auth_result(self,user,passwrd):
        data = {
            'action':'auth',
            'username':user,
            'password':passwrd,
        }

        self.sock.send(json.dumps(data).encode("utf-8"))
        response = self.get_response()
        if response.get('status_code') == 254:
            print("Passed authentication!")
            self.user = user
            return True
        else:
            print(response.get("status_msg"))

    def get_response(self):
        data = self.sock.recv(1024)
        data = json.loads(data.decode("utf-8"))

    def interactive(self):
        if self.authenticate():
            print("start interactive..")
            while True:
                choice = input("[%s]:" %self.user).strip()
                if len(choice) == 0:continue
                cmd_list = choice.split()
                if hasattr(self,"_%s" %cmd_list[0]):
                    func = getattr(self,"_%s" %cmd_list[0])
                    func(cmd_list)
                else:
                    print("Invalid cmd.")

    def _md5_required(self,cmd_list):
        if '--md5' in cmd_list:
            return True

    def show_progress(self,total):
        received_size = 0
        current_percent = 0
        while received_size < total:
            if int((received_size / total) * 100) >current_percent:
                print("#",end="",flush=True)
                current_percent = (received_size / total) * 100
            new_size = yield
            received_size += new_size

    def _get(self,cmd_list):
        print("get--",cmd_list)
        if len(cmd_list) == 1:
            print("no filename follows..")
            return
        data_header = {
            'action':'get',
            'filename':cmd_list[1],
        }

        if self._md5_required(cmd_list):
            data_header['md5'] = True

        self.sock.send(json.dumps(data_header).encode("utf-8"))
        response = self.get_response()
        print(response)

        if response["status_code"] == 257:
            self.sock.send(b'1')
            base_filename = cmd_list[1].split('/')[-1]
            received_size = 0
            file_obj = open(base_filename,'wb')

            if self._md5_required(cmd_list):
                md5_obj = hashlib.md5()

                progress = self.show_progress(response['file_size'])
                progress.__next__()

                while received_size <response['file_size']:
                    data = self.sock.recv(4096)
                    received_size += len(data)

                    try:
                        progress.send(len(data))
                    except StopIteration as e:
                        print("100%")

                    file_obj.write(data)
                    md5_obj.update(data)

                else:
                    print("--->file rece done<---")
                    file_obj.close()
                    md5_val = md5_obj.hexdigest()
                    md5_from_server = self.get_response()
                    if md5_from_server['status_code'] == 258:
                        if md5_from_server['md5'] == md5_val:
                            print("%s 文件一致性校验成功！" % base_filename)
            else:
                progress = self.show_progress(response['file_size'])
                progress.__next__()

                while received_size < response['file_size']:
                    data = self.sock.recv(4096)
                    received_size += len(data)
                    file_obj.write(data)
                    try:
                        progress.send(len(data))
                    except StopIteration as e:
                        print("100%")
                else:
                    print("--->file rece done<---")
                    file_obj.close()

    def _put(self,cmd_list):
        print("put--",cmd_list)
        if len(cmd_list) == 1:
            print("no filename follows...")
            return
        data_header = {
            'action':'put',
            'filename':cmd_list[1],
        }
        self.sock.send(json.dumps(data_header).encode())
        self.sock.recv(1)
        file_obj = open(cmd_list[1], 'br')
        for line in file_obj:
            self.sock.send(line)


if __name__ == '__main__':
    ftp = FTPClient()
    ftp.interactive()








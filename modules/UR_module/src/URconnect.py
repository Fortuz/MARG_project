import socket
import time

class URCom:
    def __init__(self,ip,port):
        self.ip=ip
        self.port=port
        self.buffsize=2048
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.isconnected=False

    def conn(self):
        self.s.connect((self.ip, self.port))
        self.isconnected=True

    def recv(self):
        adat=self.s.recv(self.buffsize)
        self.lastrec=time.time()
        return adat

    def send(self,data):
        self.s.send(data.encode("UTF-8"))

    def sendbinary(self,data):
        self.s.send(data)
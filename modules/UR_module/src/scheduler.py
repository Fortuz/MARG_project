#encoding: utf-8
import numpy as np
from RTDEhandler import RTDEhandler
from URconnect import URCom
import socket
from threading import Thread
import time
from queue import Queue

class scheduler:
    def __init__(self, robotip):
        self.robot=URCom(robotip,30002)
        self.servsock=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.IP=socket.gethostbyname(socket.gethostname())
        self.rtde=RTDEhandler(robotip)
        self.rtde.send_recipe('actual_TCP_pose')
        self.rtde.start_comm()
        self.rtde.get_data()
        self.posinfo=[]
        self.posqueue=[True, Queue(maxsize=1000)]

    def saveposinfo(self,filename):
        np.savetxt(filename,np.round(np.array(self.posinfo).reshape(-1,7),decimals=6),delimiter=",")

    def resetposinfo(self):
        self.posinfo=[]

    def monitorpos(self,sleeptime):
        while True:
            self.posqueue[1].put(np.array([time.time()]+[x for x in self.rtde.get_data()]))
            #self.posinfo.append(np.array([time.time()]+[x for x in self.rtde.get_data()]))
            time.sleep(sleeptime)

    def startmonitor(self,sleeptime):
        Thread(target=self.monitorpos, args=[sleeptime]).start()

    def load_testdata(self, testplan, points):
        with open(testplan, 'r') as f:
            pathlines = f.readlines()

        with open(points, 'r') as f:
            pointlines = f.readlines()

        self.pointdict = {}
        for point in pointlines:
            params = point.split(',')
            self.pointdict[params[0]] = np.array([float(x) for x in params[1:]])

        self.times = []
        self.pathlists = []
        self.speeds = []
        self.accs = []
        for path in pathlines:
            params = path.split('\t')
            self.pathlists.append(params[0].split(','))
            self.times.append(float(params[1]))
            self.speeds.append(params[2])
            self.accs.append(params[3])

    def blockit(self):
        self.server.recv(400)

    def sendgoto(self, goal, v, a):
        preproc=np.round(goal,decimals=4)
        cmd=",".join(['gotol']+[str(x) for x in preproc]+[str(v),str(a)])+'\n'
        print(cmd)
        self.server.send(cmd.encode('ASCII'))

    def sendwait(self,time):
        cmd = ",".join(['wait',str(time)])+'\n'
        print(cmd)
        self.server.send(cmd.encode('ASCII'))

    def connect(self):
        self.robot.conn()

        robotprog = open('robotprog.txt', 'r')
        robotprog = robotprog.read()
        robotprog = robotprog.replace('//GEPIP//', self.IP)
        self.robot.send(robotprog)
        print(robotprog)

        self.servsock.bind((self.IP, 12345))
        print("Bind")
        self.servsock.listen(1)
        print("listen")
        self.server, self.client_address = self.servsock.accept()
        print("Accept")

        self.sendgoto(self.pointdict["home"],300,300)
        self.blockit()

    def protocol(self, startcycle, endcycle):
        for i in range(len(self.pathlists)):
            input("Press Enter to start observation")
            startcycle()
            stime=time.time()
            first = True
            while time.time()-stime<self.times[i]:
                for pos in self.pathlists[i]:
                    self.step(self.pointdict[pos],self.speeds[i],self.accs[i],skip=first)
                    if first:
                        first = False

            self.sendgoto(self.pointdict["home"], 300, 300)
            self.blockit()
            endcycle()

            input("Press Enter to start measurement")
            startcycle()
            stime = time.time()
            first = True
            while time.time() - stime < self.times[i]:
                for pos in self.pathlists[i]:
                    self.step(self.pointdict[pos], self.speeds[i], self.accs[i], skip=first)
                    if first:
                        first = False

            self.sendgoto(self.pointdict["home"], 300, 300)
            self.blockit()
            endcycle()


    def start(self, startcylce, endcycle):
        Thread(target=self.protocol, args=[startcylce, endcycle]).start()

    def step(self, nextpos, speed, acc, skip=False):
        currpos = np.array(self.rtde.get_data())

        currtop = currpos
        currtop[2] += 0.15
        nexttop = nextpos.copy()
        nexttop[2] += 0.15

        if not skip:
            self.sendgoto(currtop, speed, acc)
            self.blockit()
            self.sendgoto(nexttop, speed, acc)
            self.blockit()
        self.sendgoto(nextpos, speed, acc)
        self.blockit()


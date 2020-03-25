<<<<<<< Updated upstream
#encoding: utf-8
#This file is the main python file for UR one line commands
import numpy as np
from URconnect import URCom
from RTDEhandler import RTDEhandler
import time

def linearmotion(startp, endp, orientation, n = 1):
    robot = URCom("10.0.0.111",30002)
    #Csatlakozás létesítése, itt kell a robotot remote-módba kapcsolni
    robot.conn()
    #Egy parancs kiküldése, lezárás \n-nel
    # Az 1. pont koordinátái
    p1 = np.concatenate((startp, orientation))
    # A 2. pont koordinátái
    p2 = np.concatenate((endp, orientation))
    
    for i in range(n)
        #robot.send("movel(p[%f,%f,%f,%f,%f,%f])\n")
        robot.send("movel(p" + str(p1.tolist) + ")\n")
        robot.send("movel(p" + str(p2.tolist) + ")\n")
        



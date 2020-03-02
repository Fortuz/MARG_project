#encoding: utf-8
#This file is the main python file for UR one line commands
import numpy as np
from URconnect import URCom
from RTDEhandler import RTDEhandler
import time

'''
#Command Port: 30002
#Üres socket létrehozása
robot = URCom("10.0.0.111",30002)
#Csatlakozás létesítése, itt kell a robotot remote-módba kapcsolni
robot.conn()
#Egy parancs kiküldése, lezárás \n-nel
robot.send("movej(p[0.1,-0.3,0.0,0,-3,1])\n")
'''

'''
#Command Port: 30002
#Üres socket létrehozása
robot = URCom("10.0.0.111",30002)
#Csatlakozás létesítése, itt kell a robotot remote-módba kapcsolni
robot.conn()
#Egy parancs kiküldése, lezárás \n-nel
f = open("./robotprog_konzi.txt","r")
robotprog=f.read()
robot.send(robotprog)
'''

#'''
rtde = RTDEhandler("10.0.0.111")
rtde.send_recipe("actual_TCP_pose")
rtde.start_comm()
while True:
    time.sleep(1)
    print(rtde.get_data())

#'''
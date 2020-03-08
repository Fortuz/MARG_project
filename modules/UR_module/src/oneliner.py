<<<<<<< Updated upstream
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
=======
<<<<<<< Updated upstream
#This file is the main python file for UR one line commands
#encoding: utf-8

import numpy as np

from URconnect import URCom

robot= URCom("10.0.0.111",30002)
robot.conn()
f= open("./robot.txt","r")
robotprog=f.read()
robot.send("movej(p[0.1,-0.5,0.8,0,-1,1])\n")


=======
#This file is the main python file for UR one line command

from URconnect import URCom


#mat = np.ones((10,10))
#mat *= 3
#mat *= 2  #konstans szorzás
#mat -= np.ones((3,3))
#mat2 = np.ones((3,3))*10

#mat=mat @ mat2.T # @mátrix szorzás T transzpoonált

#print(mat)

robot = URCom("10.0.0.111",30002)  #ip és port üres socket létrehozása
robot.conn() #csatlakozás létesítése itt kell robotot remote módba kapcsolni
robot.send("movej(p[0.2,-0.,0.4,0,-3,1])\n") #parancs küldése és újsor xyz rx ry rz
>>>>>>> Stashed changes
>>>>>>> Stashed changes

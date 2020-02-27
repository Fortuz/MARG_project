import URconnect
import struct
import select

class RTDEhandler:
    def __init__(self,ip="10.0.0.121"):

        self.robot=URconnect.URCom(ip,30004)
        self.robot.conn()
        self.typedict = {}
        self.typedict["DOUBLE"] = 'd'
        self.typedict["VECTOR6D"] = '6d'
        self.frm=""

    def send_recipe(self,recipe="timestamp,joint_temperatures"):
        varlist = recipe.encode("utf-8")
        varlen = len(varlist)
        packtype = 79
        msg = struct.pack(">HB", varlen + 3, packtype) + varlist
        self.robot.sendbinary(msg)
        uzi = self.robot.recv()
        uzi = uzi[3:]
        vartypes = uzi.decode('utf-8').split(',')

        self.frm = '>'
        for t in vartypes:
            self.frm += self.typedict[t]

        self.robot.buffsize=struct.calcsize(self.frm)+3
        return uzi

    def start_comm(self):
        msg = struct.pack(">HB", 3, 83)
        self.robot.sendbinary(msg)
        uzi = self.robot.recv()
        return uzi

    def get_data(self):
        self.robot.buffsize = (struct.calcsize(self.frm) + 3) * 10000
        r, _, _ = select.select([self.robot.s], [], [], 0)
        #print(self.robot.s)
        #print(r)
        while self.robot.s in r:
            self.robot.recv()
            r, _, _ = select.select([self.robot.s], [], [], 0)
        self.robot.buffsize = struct.calcsize(self.frm) + 3
        uzi = self.robot.recv()
        uzi = uzi[3:]
        padbytes = len(uzi) - struct.calcsize(self.frm)
        if padbytes > 0:
            tempfrm = self.frm + str(padbytes) + "x"
        else:
            tempfrm = self.frm
        return struct.unpack(tempfrm, uzi)


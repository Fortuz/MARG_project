# -*- coding: utf-8 -*-
"""

voidonSpatialData(self, acceleration, angularRate, magneticField, timestamp)

The most recent values that your channel has measured will be reported in this
event, which occurs when the DataInterval has elapsed.

self(type: Spatial):object which sent the event
acceleration(type: list[float]):The acceleration vaulues
angularRate(type: list[float]):The angular rate values
magneticField(type: list[float]):The field strength values
timestamp(type: float):The timestamp value

"""
from Phidget22.Phidget import *
from Phidget22.Devices.Spatial import *
import time
import numpy as np


array = []

def onSpatialData(self, acceleration, angularRate, magneticField, timestamp):
	array.append([timestamp,acceleration[0],acceleration[1], acceleration[2],angularRate[0],angularRate[1],angularRate[2], magneticField[0], magneticField[1], magneticField[2]])

ch = Spatial()
# Register for event before calling open
ch.setOnSpatialDataHandler(onSpatialData)
print("Waiting for the Phidget TemperatureSensor Object to be attached...")
ch.openWaitForAttachment(5000)			# időtúllépés 5 s
ch.setDataInterval(20)					# 20 ms a mintavételezési idő
ch.open()

# enter-ig olvas
try:
		input("Press Enter to Stop\n")
except (Exception, KeyboardInterrupt):
		pass
ch.close()


np.savetxt('data.csv', array,fmt='%10.6f', delimiter=',', newline='\n', comments='')
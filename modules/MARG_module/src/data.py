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

def onSpatialData(self, acceleration, angularRate, magneticField, timestamp):
	print("Acceleration: " + str(acceleration))
	print("AngularRate: " + str(angularRate))
	print("MagneticField: " + str(magneticField))
	print("Timestamp: " + str(timestamp))

ch = Spatial()

# Register for event before calling open
ch.setOnSpatialDataHandler(onSpatialData)

ch.open()

while True:
	# Do work, wait for events, etc.
	time.sleep(1)

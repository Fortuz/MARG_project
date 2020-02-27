from mocapreader import Mocapreader
import time
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import numpy as np

mocap = Mocapreader([1,2])

mocap.run()
time.sleep(10)
print(mocap.datalog)


x=[]
y=[]
z=[]
for pos in mocap.datalog:
    x.append(pos[0])
    y.append(pos[1])
    z.append(pos[2])

x=np.array(x)
y=np.array(y)
z=np.array(z)

print(np.average(x),np.average(y),np.average(z))

fig = plt.figure()
ax = fig.add_subplot(111,projection="3d")
ax.view_init(azim=180)
ax.plot(x,z,y)
ax.set_xlabel("x")
ax.set_ylabel('z')
ax.set_zlabel('y')
plt.show()

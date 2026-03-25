
import pybullet as p
import pybullet_data
p.connect(p.DIRECT)
p.setAdditionalSearchPath(pybullet_data.getDataPath())
t = p.loadURDF('table/table.urdf', basePosition=[0.5,0,0], globalScaling=0.6, useFixedBase=True)
aabb = p.getAABB(t)
print('Table AABB min:', aabb[0])
print('Table AABB max:', aabb[1])
print('Table top Z:', aabb[1][2])
p.disconnect()

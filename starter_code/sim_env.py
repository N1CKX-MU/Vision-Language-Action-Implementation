import pybullet as p
import pybullet_data
import numpy as np
import math
import time

class SimEnv:
    IMG_W = 640
    IMG_H = 480
    FOV   = 60.0

    def __init__(self, gui=True):
        self.client = p.connect(p.GUI if gui else p.DIRECT)
        p.setAdditionalSearchPath(pybullet_data.getDataPath())
        p.setGravity(0, 0, -9.81)

        # Ground plane
        p.loadURDF("plane.urdf")

        # Table
        self.table = p.loadURDF(
            "table/table.urdf",
            basePosition=[0.5, 0, 0],
            globalScaling=0.6,
            useFixedBase=True,
        )

        # Spawn coloured objects
        self.objects = self._spawn_objects()

        # Camera intrinsics
        self.K = self._build_K()

        print("[SimEnv] Ready. Objects:", list(self.objects.keys()))

    def _build_K(self):
        fx = fy = (self.IMG_W / 2) / math.tan(math.radians(self.FOV / 2))
        cx, cy  = self.IMG_W / 2, self.IMG_H / 2
        return np.array([[fx, 0, cx],
                         [ 0,fy, cy],
                         [ 0, 0,  1]], dtype=np.float64)

    def _spawn_objects(self):
        objects = {}

        colours = {
            "red_cube":    ([1, 0, 0, 1],    [0.35, -0.15, 0.376 + 0.025], "cube"),
            "blue_bowl": ([0, 0.4, 1, 1], [0.55, 0.15, 0.376 + 0.015], "cylinder"),
            "green_cube":  ([0, 0.8, 0, 1],  [0.60, -0.10, 0.376 + 0.025], "cube"),
            "yellow_cube": ([1, 0.9, 0, 1],  [0.40,  0.20, 0.376 + 0.025], "cube"),
        }

        for name, (rgba, pos, shape) in colours.items():
            if shape == "cube":
                col = p.createCollisionShape(p.GEOM_BOX,    halfExtents=[0.025]*3)
                vis = p.createVisualShape(   p.GEOM_BOX,    halfExtents=[0.025]*3, rgbaColor=rgba)
            elif shape == "cylinder":
                col = p.createCollisionShape(p.GEOM_CYLINDER, radius=0.05, height=0.03)
                vis = p.createVisualShape(   p.GEOM_CYLINDER, radius=0.05, length=0.03, rgbaColor=rgba)
            else:
                col = p.createCollisionShape(p.GEOM_SPHERE, radius=0.04)
                vis = p.createVisualShape(   p.GEOM_SPHERE, radius=0.04,           rgbaColor=rgba)

            body = p.createMultiBody(
                baseMass=0.1,
                baseCollisionShapeIndex=col,
                baseVisualShapeIndex=vis,
                basePosition=pos,
            )
            objects[name] = {"id": body, "pos": pos}

        return objects

    def get_camera_image(self):
        cam_pos    = [0.5, 0,   1.5]
        cam_target = [0.5, 0,   0.376]   # point at table surface, not 0.63
        cam_up     = [0,   1,   0  ]

        view = p.computeViewMatrix(cam_pos, cam_target, cam_up)
        proj = p.computeProjectionMatrixFOV(
            fov=self.FOV, aspect=self.IMG_W/self.IMG_H,
            nearVal=0.01, farVal=10.0,
        )
        _, _, rgba, depth_buf, _ = p.getCameraImage(
            self.IMG_W, self.IMG_H, view, proj,
            renderer=p.ER_TINY_RENDERER,
        )

        rgb = np.array(rgba, dtype=np.uint8).reshape(self.IMG_H, self.IMG_W, 4)[:,:,:3]

        near, far = 0.01, 10.0
        d = np.array(depth_buf, dtype=np.float32).reshape(self.IMG_H, self.IMG_W)
        depth = far * near / (far - (far - near) * d)

        return rgb, depth, self.K

    def move_to_pose(self, x, y, z, roll=0, pitch=0, yaw=0):
        print(f"  [sim] move_to_pose({x:.3f}, {y:.3f}, {z:.3f})")
        # We'll add real IK here in a later step
        time.sleep(0.5)

    def set_gripper(self, open: bool):
        print(f"  [sim] gripper {'open' if open else 'closed'}")

    def close(self):
        p.disconnect(self.client)

if __name__ == "__main__":
    env = SimEnv(gui=True)

    print("Camera K matrix:")
    print(env.K)

    rgb, depth, K = env.get_camera_image()
    print(f"RGB shape  : {rgb.shape}")
    print(f"Depth range: {depth.min():.3f} – {depth.max():.3f} m")

    import cv2
    cv2.imwrite("test_rgb.jpg",   cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR))
    cv2.imwrite("test_depth.jpg", (depth * 50).astype(np.uint8))
    print("Saved test_rgb.jpg and test_depth.jpg")
    print("Close the PyBullet window to quit")

    # Keep stepping so GUI stays responsive
    while p.isConnected(env.client):
        p.stepSimulation()
        time.sleep(1./240.)
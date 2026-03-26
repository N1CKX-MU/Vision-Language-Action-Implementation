import pybullet as p
import pybullet_data
import numpy as np
import math
import time
import cv2

class SimEnv:
    """
    The Simulation Environment: Wraps PyBullet to provide a high-level API for 
    robot control and perception. Simulates the environment for Robotic Arm and all the objects in the scene
    """

    IMG_W = 640
    IMG_H = 480
    FOV   = 60.0

    def __init__(self, gui=True):
        #Initialize Physics Client: GUI for visual simulation, DIRECT for faster, headless execution
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
        # Load in Panda Arm
        self.robot = p.loadURDF(
            "franka_panda/panda.urdf",
             basePosition=[0.09, 0.0, 0.376 ],
              useFixedBase=True
        )
        
        # PyBullet specific link indices for the Panda arm
        self.end_effector_idx = 11  # The tip of the arm between the fingers
        self.gripper_indices = [9, 10] # The left and right fingers

        # Spawn coloured objects
        self.objects = self._spawn_objects()

        # Reset to home joints 
        home_joints = [-1.57, -0.785, 0.0, -2.356, 0.0, 1.571, 0.785]
        for i in range(7):
            p.resetJointState(self.robot, i, home_joints[i])

        # Camera intrinsics
        self.K = self._build_K()

        print("[SimEnv] Ready. Objects:", list(self.objects.keys()))

    def _build_K(self):
        """
        Calculates the Camera intrinsic Matric (K) using the Pin Hole Model.
        Used by Projection Module to map pixels to 3D points
        """
        fx = fy = (self.IMG_H / 2) / math.tan(math.radians(self.FOV / 2))
        cx, cy  = self.IMG_W / 2, self.IMG_H / 2
        return np.array([[fx, 0, cx],
                         [ 0,fy, cy],
                         [ 0, 0,  1]], dtype=np.float64)

    def _spawn_objects(self):
        """
        Randomizes the workspace with target objects
        objects include : { 3 Cubes of different colours, 1 custom bowl URDF(destination)}
        """
        objects = {}

        colours = {
            "red_cube":    ([1, 0, 0, 1],    "cube"),
            "blue_bowl":   ([0, 0.4, 1, 1],  "bowl"),
            "green_cube":  ([0, 0.8, 0, 1],  "cube"),
            "yellow_cube": ([1, 0.9, 0, 1],  "cube"),
        }

        # Safe area on the table for spawning objects
        x_min, x_max = 0.35, 0.65
        y_min, y_max = -0.25, 0.25
        min_dist = 0.1 # Minimum distance between objects to prevent overlapping

        spawned_positions = []
        # Randomize the Postions inside the workspace of the robotic arm
        for name, (rgba, shape) in colours.items():
            valid_pos = False
            for _ in range(100):
                x = np.random.uniform(x_min, x_max)
                y = np.random.uniform(y_min, y_max)
                
                if all(math.hypot(x - sx, y - sy) >= min_dist for sx, sy in spawned_positions):
                    valid_pos = True
                    break
            
            if not valid_pos:
                x = np.random.uniform(x_min, x_max)
                y = np.random.uniform(y_min, y_max)
                
            spawned_positions.append((x, y))
            
            z = 0.376 + (0.025 if shape == "cube" else 0.015)
            pos = [x, y, z]

            if shape == "bowl":
                body = p.loadURDF("urdf/bowl.urdf", basePosition=pos)
                objects[name] = {"id": body, "pos": pos}
            else:
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
        """
        Captures a synthetic RGB-D snapshot of the worksapce
        Returns: RGB Image, Depth Map, and Intrinsics(K)
        """
        cam_pos    = [0.5, 0,   1.5]
        cam_target = [0.5, 0,   0.376]   
        cam_up     = [0,   1,   0  ]

        view = p.computeViewMatrix(cam_pos, cam_target, cam_up)
        # Build Projection Matrix
        proj = p.computeProjectionMatrixFOV(
            fov=self.FOV, aspect=self.IMG_W/self.IMG_H,
            nearVal=0.01, farVal=10.0,
        )
        # Capture Image
        _, _, rgba, depth_buf, _ = p.getCameraImage(
            self.IMG_W, self.IMG_H, view, proj,
            renderer=p.ER_TINY_RENDERER,
        )
        # Convert to RGB
        rgb = np.array(rgba, dtype=np.uint8).reshape(self.IMG_H, self.IMG_W, 4)[:,:,:3]
        # Convert depth buffer to meters
        near, far = 0.01, 10.0
        d = np.array(depth_buf, dtype=np.float32).reshape(self.IMG_H, self.IMG_W)
        depth = far * near / (far - (far - near) * d)
        return rgb, depth, self.K

    def move_to_pose(self, x, y, z, roll=0, pitch=0, yaw=0, wait=True):
        """
        Moves the robot end-effector to a target (x,y,z) using Inverse Kinematics

        Math: p.calculateInverseKinematics solves for the 7 joint angles required to reach the target pose
        6-DOF pose goal: we use vertical orientation [pi,0,0] for a top down grasp
        """

        print(f"  [sim] Moving arm to ({x:.3f}, {y:.3f}, {z:.3f})")

        ll = [-2.8973, -1.7628, -2.8973, -3.0718, -2.8973, -0.0175, -2.8973]
        ul = [ 2.8973,  1.7628,  2.8973, -0.0698,  2.8973,  3.7525,  2.8973]
        jr = [u - l for u, l in zip(ul, ll)]
        
        # Run IK multiple times from different seeds, pick best solution
        best_joints = None
        best_error  = float('inf')

        # 1. Define Orientation
        # For a top-down grasp, the Panda end-effector Z-axis must point straight down.
        # Euler [pi, 0, 0] flips the hand 180° around X so the fingers face the table.
        orientation = p.getQuaternionFromEuler([math.pi + roll, pitch, yaw])
        natural_posture = [0.0, -0.785, 0.0, -2.356, 0.0, 1.571, 0.785]

        # 2. Calculate Inverse Kinematics (IK)
        joint_poses = p.calculateInverseKinematics(
            bodyUniqueId=self.robot,
            endEffectorLinkIndex=self.end_effector_idx,
            targetPosition=[x, y, z],
            restPoses=natural_posture,
            targetOrientation=orientation,
            lowerLimits=ll,
            upperLimits=ul,
            jointRanges=jr,
            maxNumIterations=200,
            residualThreshold=1e-5
        )

        # Score = deviation from natural posture
        error = sum((joint_poses[i] - natural_posture[i])**2 for i in range(7))
        if error < best_error:
            best_error  = error
            best_joints = joint_poses

        # 3. Command the motors to move to those joint angles
        for i in range(7): 
            p.setJointMotorControl2(
                bodyIndex=self.robot,
                jointIndex=i,
                controlMode=p.POSITION_CONTROL,
                targetPosition=joint_poses[i],
                force=240,
                maxVelocity=0.5
            )

        # 4. Step the simulation long enough for the arm to converge
        if wait:
            for _ in range(720):  # ~2 seconds at 240Hz
                p.stepSimulation()
                time.sleep(1./240.)
                # current = p.getLinkState(
                # self.robot, self.end_effector_idx,
                # physicsClientId=self.client
                # )[0]
                # error = sum((current[i] - [x,y,z][i])**2 for i in range(3))**0.5
                # if error < 0.005:  # 5mm tolerance
                #     break
        else:
            for _ in range(50):
                p.stepSimulation()
                time.sleep(1./240.)

    def set_gripper(self, open: bool):
        """
        Controls the prismatic gripper joints.
        0.04 = Fully Open | 0.0 = Fully Closed
        """
        print(f"  [sim] Gripper {'opening' if open else 'closing'}...")
        
        # Target position for the fingers: 0.04m (open) or 0.0m (closed/pinched)
        target_pos = 0.04 if open else 0.0 

        for joint_idx in self.gripper_indices:
            p.setJointMotorControl2(
                bodyIndex=self.robot,
                jointIndex=joint_idx,
                controlMode=p.POSITION_CONTROL,
                targetPosition=target_pos,
                force=100 # Gripping force
            )

        
        for _ in range(60): 
            p.stepSimulation()
            time.sleep(1./240.)

    def close(self):
        p.disconnect(self.client)

if __name__ == "__main__":
    env = SimEnv(gui=True)

    print("Camera K matrix:")
    print(env.K)

    rgb, depth, K = env.get_camera_image()
    print(f"RGB shape  : {rgb.shape}")
    print(f"Depth range: {depth.min():.3f} – {depth.max():.3f} m")

    
    cv2.imwrite("test_rgb.jpg",   cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR))
    cv2.imwrite("test_depth.jpg", (depth * 50).astype(np.uint8))
    print("Saved test_rgb.jpg and test_depth.jpg")
    print("Close the PyBullet window to quit")

    # Keep stepping so GUI stays responsive
    while p.isConnected(env.client):
        p.stepSimulation()
        time.sleep(1./240.)
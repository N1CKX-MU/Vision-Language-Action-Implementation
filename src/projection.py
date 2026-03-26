import numpy as np 
import pybullet as p 

class ProjectionModule:
    """
    Handles the geometric transformation of pixels to 3D world coordinates. 
    using the intrinsic matrix of the camera and using the pinhole camera model
    """
    def __init__(self, cam_pos, cam_target, cam_up):
        self.cam_pos = cam_pos
        self.cam_target = cam_target
        self.cam_up = cam_up

    def pixel_to_camera_frame(self,u: int,v: int,depth: np.ndarray,K: np.ndarray) -> tuple :
        """
        De-projects a pixel , (u,v) into the Camera's Local Coordinate System

        Math: based on Pinhole Model

        X = (u - cx) * Z / fx
        Y = (v - cy) * Z / fy
        Z = depth

        """
        Z = float(depth[v,u])

        if Z <= 0 or np.isnan(Z):
            raise ValueError("Invalid depth value")
        
        fx = K[0,0]
        fy = K[1,1]
        cx = K[0,2]
        cy = K[1,2]

        X = (u - cx) * Z / fx
        Y = (v - cy) * Z / fy

        return X, Y, Z

    # def camera_to_world_frame(self, X_c: float, Y_c: float, Z_c: float) -> tuple :
    #     """
        
    #     """
    #     view = p.computeViewMatrix(self.cam_pos, self.cam_target, self.cam_up)
    #     V = np.array(view).reshape(4,4)
    #     V_inv = np.linalg.inv(V)

    #     point_h = np.array([X_c, -Y_c, -Z_c, 1.0])
    #     world_h = V_inv @ point_h

    #     return float(world_h[0]), float(world_h[1]), float(world_h[2])

    def camera_to_world_frame(self, X_c: float, Y_c: float, Z_c: float) -> tuple:
        """
        Converts a point from the OpenCV camera's reference frame to the global simulator frame
        using explicit basis vectors. This avoids PyBullet's matrix layout bugs.
        """
        cam_pos = np.array(self.cam_pos, dtype=np.float64)
        cam_target = np.array(self.cam_target, dtype=np.float64)
        cam_up = np.array(self.cam_up, dtype=np.float64)

        #  Calculate camera's forward axis pointing into the scene
        forward = cam_target - cam_pos
        forward /= np.linalg.norm(forward)

        #  Calculate camera's right axis (+X)
        right = np.cross(forward, cam_up)
        right /= np.linalg.norm(right)

        #  calculate camera's true up axis
        up = np.cross(right, forward)

        #  construct Rotation matrix mapping OpenCV axes to World axes
        # OpenCV: +X is right, +Y is DOWN (so we use -up), +Z is FORWARD
        R = np.column_stack([right, -up, forward])

        #  rotate the point and add the camera's translation offset
        point_c = np.array([X_c, Y_c, Z_c])
        point_world = R @ point_c + cam_pos

        return float(point_world[0]), float(point_world[1]), float(point_world[2])

    def get_world_coordinates(self, u : int, v : int, depth : np.ndarray, K : np.ndarray) -> tuple :
        """
        Wrapper to perform the 2D -> 3D pipeline in one call 
        """
        X_c, Y_c, Z_c = self.pixel_to_camera_frame(u, v, depth, K)
        return self.camera_to_world_frame(X_c, Y_c, Z_c)


if __name__ == "__main__":
    import sys, os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
    from starter_code.sim_env import SimEnv
    
    CAM_POS    = [0.5, 0.0, 1.5]
    CAM_TARGET = [0.5, 0.0, 0.376]
    CAM_UP     = [0.0, 1.0, 0.0]

    env = SimEnv(gui=False)
    rgb, depth, K = env.get_camera_image()
    
    projector = ProjectionModule(CAM_POS, CAM_TARGET, CAM_UP)
    
    test_pixels = {
        "red_cube":    (263, 295),
        "blue_bowl":   (338, 180),
        "green_cube":  (362, 275),
        "yellow_cube": (280, 158),
    }

    expected = {
        "red_cube":    [0.35, -0.15],
        "blue_bowl":   [0.55,  0.15],
        "green_cube":  [0.60, -0.10],
        "yellow_cube": [0.40,  0.20],
    }

    print(f"{'Object':15s}  {'Pixel (u,v)':15s}  {'Calculated (X, Y)':>18}  {'Expected (X, Y)'}")
    print("-" * 75)

    # Test if the predicted and expected are approximately the same

    for name, (u, v) in test_pixels.items():
        Xw, Yw, Zw = projector.get_world_coordinates(u, v, depth, K)
        ex, ey = expected[name]
        print(f"{name:15s}  ({u:3d}, {v:3d})         ({Xw:5.2f}, {Yw:5.2f})          ({ex:5.2f}, {ey:5.2f})")

    env.close()
    

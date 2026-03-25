import numpy as np 

def pixel_to_world(u,v,depth,K):
    """

    """

    Z = float(depth[v,u])

    if Z <= 0 or np.isnan(Z):
        raise ValueError("Invalid depth value")
    
    fx = K[0,0]
    fy = K[1,1]
    cx = K[0,2]
    cy = K[1,2]

    X = (u - cx) * Z / fx
    Y = (v - cy ) * Z / fy

    return X,Y,Z

def camera_to_world(X_c, Y_c, Z_c, cam_pos, cam_target, cam_up):
    """
    Convert camera frame point to world frame.
    Reconstructs the rotation matrix from the same look-at params
    PyBullet uses for computeViewMatrix.
    """
    cam_pos    = np.array(cam_pos,    dtype=np.float64)
    cam_target = np.array(cam_target, dtype=np.float64)
    cam_up     = np.array(cam_up,     dtype=np.float64)

    # Same axes PyBullet uses internally
    z = cam_pos - cam_target;  z /= np.linalg.norm(z)
    x = np.cross(cam_up, z);   x /= np.linalg.norm(x)
    y = np.cross(z, x)

    # Rotation: camera axes as columns
    R = np.column_stack([x, y, z])

    point_world = R @ np.array([X_c, Y_c, Z_c]) + cam_pos
    return point_world

if __name__ == "__main__":
    from starter_code.sim_env import SimEnv
    import pybullet as pitch

    env = SimEnv(gui=False) # only get the image out without turning on the GUI
    rgb, depth, K = env.get_camera_image()

    print("K Matrix: ")
    print(K)
    print()

     # Test: project the centre of each known object
    # We know their world positions from _spawn_objects
    test_pixels = {
        "red_cube":    (263, 295),   # approximate pixel from the image
        "blue_bowl":   (338, 180),
        "green_cube":  (362, 275),
        "yellow_cube": (280, 158),
    }

    for name, (u, v) in test_pixels.items():
        X, Y, Z = pixel_to_world(u, v, depth, K)
        print(f"{name:15s} pixel=({u},{v})  →  camera frame X={X:.3f} Y={Y:.3f} Z={Z:.3f}")

    env.close()
     
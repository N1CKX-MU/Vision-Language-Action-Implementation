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
    Convert camera frame point to world frame using PyBullet's
    actual view matrix (inverted). This avoids any axis convention guesswork.
    """
    import pybullet as p

    view = p.computeViewMatrix(cam_pos, cam_target, cam_up)
    # PyBullet returns column-major 4x4
    V = np.array(view).reshape(4, 4).T

    # V is world->camera, so invert it to get camera->world
    V_inv = np.linalg.inv(V)

    # PyBullet camera has Y flipped vs standard OpenCV convention
    point_h = np.array([X_c, -Y_c, -Z_c, 1.0])
    world_h = V_inv @ point_h

    return float(world_h[0]), float(world_h[1]), float(world_h[2])


# def camera_to_world(X_c, Y_c, Z_c, cam_pos, cam_target, cam_up):
#     """
   
#     """
#     cam_pos    = np.array(cam_pos,    dtype=np.float64)
#     cam_target = np.array(cam_target, dtype=np.float64)
#     cam_up     = np.array(cam_up,     dtype=np.float64)

#     # Same axes PyBullet uses internally
#     z = cam_pos - cam_target;  z /= np.linalg.norm(z)
#     x = np.cross(cam_up, z);   x /= np.linalg.norm(x)
#     y = np.cross(z, x)

#     # Rotation camera axes as columns
#     R = np.column_stack([x, y, z])

#     point_world = R @ np.array([X_c, Y_c, Z_c]) + cam_pos
#     return point_world

if __name__ == "__main__":

    from starter_code.sim_env import SimEnv

    CAM_POS    = [0.5, 0,  1.5]
    CAM_TARGET = [0.5, 0,  0.376]
    CAM_UP     = [0,   1,  0]

    env = SimEnv(gui=False)
    rgb, depth, K = env.get_camera_image()
    
    test_pixels = {
        "red_cube":    (263, 295),
        "blue_bowl":   (338, 180),
        "green_cube":  (362, 275),
        "yellow_cube": (280, 158),
    }

    print(f"{'object':15s}  {'pixel':12s}  {'world X':>8}  {'world Y':>8}  {'world Z':>8}  {'expected pos'}")
    print("-" * 80)

    expected = {
        "red_cube":    [0.35, -0.15],
        "blue_bowl":   [0.55,  0.15],
        "green_cube":  [0.60, -0.10],
        "yellow_cube": [0.40,  0.20],
    }

    for name, (u, v) in test_pixels.items():
        Xc, Yc, Zc = pixel_to_world(u, v, depth, K)
        Xw, Yw, Zw = camera_to_world(Xc, Yc, Zc, CAM_POS, CAM_TARGET, CAM_UP)
        ex, ey = expected[name]
        print(f"{name:15s}  ({u:3d},{v:3d})      {Xw:8.3f}  {Yw:8.3f}  {Zw:8.3f}    expected ({ex}, {ey})")

    env.close()
     
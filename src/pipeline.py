import argparse 
import time 
import os
import sys

# Add project root to sys.path to resolve imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from starter_code.sim_env import SimEnv

from src.perception import PerceptionModule
from src.projection import ProjectionModule
from src.robot_control import RobotController
import pybullet as p

CONFIG = "models/grounding_dino/GroundingDINO_SwinT_OGC.py" 
WEIGHTS = "models/grounding_dino/groundingdino_swint_ogc.pth"


CAM_POS = [0.5, 0, 1.5]
CAM_TARGET = [0.5, 0, 0.376]
CAM_UP = [0, 1, 0]

class VLAPipeline:
    def __init__(self,config_path: str, weight_path: str, cam_pos: list, cam_target: list, cam_up: list):
        """

        """
        self.config_path = config_path
        self.weight_path = weight_path
        self.cam_pos = cam_pos
        self.cam_target = cam_target
        self.cam_up = cam_up

        self.env = None
        self.perception = None
        self.projection = None
        self.controller = None

    def setup_system(self):
        """
        
        """
        print("\n[Pipeline] Setting up the system")
        self.env = SimEnv(gui=True)

        for _ in range(100):
            if self.env and hasattr(self.env, 'client'):
                p.stepSimulation(self.env.client)# <--- The fix is here
            time.sleep(1./240.)

        self.perception = PerceptionModule(self.config_path, self.weight_path)
        self.projection = ProjectionModule(self.cam_pos, self.cam_target, self.cam_up)
        self.controller = RobotController(self.env)

    def execute_task(self,prompt :str):
        """

        """

        print(f"\n{'='*60}")
        print(f"[Pipeline] Prompt : {prompt}")
        print(f"{'='*60}")

        rgb , depth , K = self.env.get_camera_image()

        print("\n[Pipeline] Running perception module")
        centroids = self.perception.get_grasp_and_place_centroids(rgb,prompt)

        if not centroids.get("target") or not centroids.get("destination"):
            print(f"[Error] couldnt find both target and destination")
            print(f"Found {centroids}")
            return False

        print(f"[Pipeline] Found Target 2D Pixel: {centroids['target']}")
        print(f"[Pipeline] Found Destination 2D Pixel: {centroids['destination']}")

        # Step 2 Projection 

        print(f"\n[Pipeline] Step 2 Projecting to 3D space...")

        target_u, target_v = centroids["target"]
        dest_u,dest_v = centroids["destination"]

        target_3d = self.projection.get_world_coordinates(target_u,target_v,depth,K)
        dest_3d = self.projection.get_world_coordinates(dest_u,dest_v,depth,K)

        print(f"[Pipeline] Target 3D: {target_3d}")
        print(f"[Pipeline] Destination 3D: {dest_3d}")

        # Step 3 Robot Control 

        print(f"\n[Pipeline] Step 3 Executing robot control...")

        self.controller.execute_pick_and_place(target_3d, dest_3d)

        print(f"\n{'='*60}")
        print(f"[Pipeline] Task completed successfully!")
        print(f"{'='*60}")

        return True


    def teardown(self):
        """
        
        """
        print("\n[Pipeline] Tearing down the system")
        if self.env:
            self.env.close()

    

if __name__ == "__main__":
    # Command Line Arguments

    parser = argparse.ArgumentParser(description="VLA Pick and Place Pipeline")
    parser.add_argument("--prompt", type=str, required=True, help="Natural Language Command")
    args = parser.parse_args()

    pipeline = VLAPipeline(CONFIG, WEIGHTS, CAM_POS, CAM_TARGET, CAM_UP)
    
    try:
        pipeline.setup_system()
        success = pipeline.execute_task(args.prompt)

        if success:
            print("\n[Pipeline] Task completed successfully")
            time.sleep(3)
    except Exception as e:
        print(f"[Error] {e}")
    finally:
        pipeline.teardown()

        
        
        
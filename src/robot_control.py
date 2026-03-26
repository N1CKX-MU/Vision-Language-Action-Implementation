import time 
class RobotController:
    """
    Manages High level state machine for the different 
    stages in the robot's manipulation task,
    Translates 3D coords into a sequence of motions:
    """
    def __init__(self, env , hover_offset = 0.1 ):
        self.env = env
        self.hover_offset = hover_offset

    def execute_pick_and_place(self, target_3d: tuple, dest_3d: tuple):
        """
        Executes the pick and place task using a sequence of movements
        """
        tx, ty, tz = target_3d
        dx, dy, dz = dest_3d

        print(f"\n [RobotController] Starting the pick place task")
        print(f"Target: ({tx:.2f}, {ty:.2f}, {tz:.2f})")
        print(f"Destination: ({dx:.2f}, {dy:.2f}, {dz:.2f})")

        
        # initialize gripper is open before moving 
        self.env.set_gripper(open=True)
        time.sleep(0.5)

        # Hover
        print(f"\n[RobotController] Moving to hover position over target")
        self.env.move_to_pose(tx, ty, tz + self.hover_offset)
        time.sleep(1)
        # descent 
        print(f"[RobotController] Descending to target")
        
        grasp_height = tz - 0.03
        # self.env.move_to_pose(tx, ty, grasp_height)
        # time.sleep(1)

        mid_height = tz + (self.hover_offset / 2)
        self.env.move_to_pose(tx, ty, mid_height,wait=False) 
        self.env.move_to_pose(tx, ty, grasp_height)
        time.sleep(1)
        
        # close gripper
        print(f"[RobotController] Closing gripper")
        
        self.env.set_gripper(open=False)
        
        time.sleep(0.5)
        # lift object

        print("\n[RobotController] Lifting object")
        self.env.move_to_pose(tx, ty, tz + self.hover_offset)
        time.sleep(0.5)
        # move to destination hover
        print("\n[RobotController] Moving to hover position over destination")
        self.env.move_to_pose(dx, dy, dz + self.hover_offset)
        time.sleep(0.5)
        # descend to destination
        print("\n[RobotController] Descending to destination")
        self.env.move_to_pose(dx, dy, dz + 0.08)
        time.sleep(0.5)
        # open gripper
        print("\n[RobotController] Opening gripper")
        self.env.set_gripper(open=True)
        time.sleep(0.5)

       
        print("\n[RobotController] Task completed retunrnign to home position")
        self.env.move_to_pose(0.3, 0.0, 0.6)

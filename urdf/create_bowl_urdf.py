import os
import math

def generate_bowl_urdf(filepath, radius=0.06, height=0.04, thickness=0.005, num_walls=12, color="0 0.4 1 1"):
    xml = ['<?xml version="1.0" ?>', '<robot name="bowl">', '  <link name="base_link">']
    
    # Base
    base_z = thickness / 2
    xml.append(f'''    <collision>
      <origin xyz="0 0 {base_z}" rpy="0 0 0"/>
      <geometry>
        <cylinder radius="{radius}" length="{thickness}"/>
      </geometry>
    </collision>
    <visual>
      <origin xyz="0 0 {base_z}" rpy="0 0 0"/>
      <geometry>
        <cylinder radius="{radius}" length="{thickness}"/>
      </geometry>
      <material name="color">
        <color rgba="{color}"/>
      </material>
    </visual>''')

    # Walls
    wall_length = 2 * radius * math.tan(math.pi / num_walls) + 0.002
    wall_height = height
    wall_x_offset = radius - thickness/2
    wall_z = height / 2

    for i in range(num_walls):
        angle = 2 * math.pi * i / num_walls
        # Position of the wall center
        x = wall_x_offset * math.cos(angle)
        y = wall_x_offset * math.sin(angle)
        # Orientation of the wall
        yaw = angle
        
        xml.append(f'''    <collision>
      <origin xyz="{x} {y} {wall_z}" rpy="0 0 {yaw}"/>
      <geometry>
        <box size="{thickness} {wall_length} {wall_height}"/>
      </geometry>
    </collision>
    <visual>
      <origin xyz="{x} {y} {wall_z}" rpy="0 0 {yaw}"/>
      <geometry>
        <box size="{thickness} {wall_length} {wall_height}"/>
      </geometry>
      <material name="color">
        <color rgba="{color}"/>
      </material>
    </visual>''')

    # Inertial
    xml.append(f'''    <inertial>
      <mass value="0.1"/>
      <inertia ixx="0.0001" ixy="0.0" ixz="0.0" iyy="0.0001" iyz="0.0" izz="0.0001"/>
    </inertial>''')

    xml.append('  </link>\n</robot>')
    
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "w") as f:
        f.write("\\n".join(xml))
        
if __name__ == "__main__":
    generate_bowl_urdf("models/bowl.urdf")
    print("Bowl URDF generated.")

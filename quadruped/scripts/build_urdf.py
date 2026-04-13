"""
build_urdf_v4.py - Transform world-space STLs to link-local coordinates.

THE KEY FIX: World-space STL + visual origin offset breaks during rotation,
because the offset rotates with the link frame. Instead, we transform each
STL's vertices from world space to link-local space and save new STL files.
Then URDF visual origin = (0,0,0) and rotation works correctly.
"""
import json
import os
import struct
import numpy as np

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_DIR = os.path.join(SCRIPT_DIR, "..", "config")
URDF_PATH = os.path.join(SCRIPT_DIR, "..", "urdf", "robot.urdf")
MESH_SRC = os.path.join(SCRIPT_DIR, "..", "urdf", "meshes_export")
MESH_DST = os.path.join(SCRIPT_DIR, "..", "urdf", "meshes_local")
MESH_REL = "meshes_local"
BASE_Z = 0.45

os.makedirs(MESH_DST, exist_ok=True)

with open(os.path.join(CONFIG_DIR, "export_manifest.json")) as f:
    manifest = json.load(f)

# ── Suffix-to-leg mapping ──
LEG_SUFFIX = {"": "rr", "_001": "fr", "_002": "rl", "_003": "fl"}
HORN_LEG = {"": "rr", "_001": "rr", "_002": "fr", "_003": "fr",
            "_004": "rl", "_005": "rl", "_006": "fl", "_007": "fl"}

# ── Body parts → base ──
BODY_STLS = [
    "horizontal_x4.stl", "horizontal_x4_001.stl",
    "horizontal_x4_002.stl", "horizontal_x4_003.stl",
    "side_x2.stl", "side_x2_001.stl",
    "legs_middle_x2.stl", "legs_middle_x2_001.stl",
]

# ── Part-to-link assignment ──
PART_TO_LINK = {
    "hip_1": "base",
    "RR__hip_2": "base",
    "hip_cup": "base",
    "hip_servo_gear": "hip",
    # servo_frame_1 gear teeth mesh with hip_servo_gear -> rotate together
    "RR__servo_frame_1": "hip",
    # Servo 2 drives upper_leg -> THIGH link
    "RR__upper_leg_x2": "thigh",
    # Servo 3 drives these -> CALF link
    "RR__lower_leg_servo_horn_x2": "calf",
    "RR__lower_leg": "calf",
    "RR__foot": "calf",
}

# ── Servo assignments (identified by proximity to servo gears) ──
SERVO_TO_LINK = {
    # Servo 1: hip servo BODY -> base (doesn't rotate)
    "29KG_Servo_DS3218MG_011": ("fl", "base"),
    "29KG_Servo_DS3218MG_005": ("fr", "base"),
    "29KG_Servo_DS3218MG_008": ("rl", "base"),
    "29KG_Servo_DS3218MG_002": ("rr", "base"),
    # Servo 2: thigh servo BODY -> hip (on the hip gear assembly)
    "29KG_Servo_DS3218MG_010": ("fl", "hip"),
    "29KG_Servo_DS3218MG_004": ("fr", "hip"),
    "29KG_Servo_DS3218MG_007": ("rl", "hip"),
    "29KG_Servo_DS3218MG_001": ("rr", "hip"),
    # Servo 3: knee servo BODY -> thigh (mounted on upper leg, moves with it)
    "29KG_Servo_DS3218MG_009": ("fl", "thigh"),
    "29KG_Servo_DS3218MG_003": ("fr", "thigh"),
    "29KG_Servo_DS3218MG_006": ("rl", "thigh"),
    "29KG_Servo_DS3218MG": ("rr", "thigh"),
}

# ── Joint positions from servo centroids ──
SERVO_POS = {
    "fl_hip": np.array([0.0649, 0.2759, 0.3332]),
    "fr_hip": np.array([0.0649, -0.0560, 0.3332]),
    "rl_hip": np.array([-0.0175, 0.2759, 0.3332]),
    "rr_hip": np.array([-0.0175, -0.0560, 0.3332]),
    "fl_thigh": np.array([0.1338, 0.2594, 0.3318]),
    "fr_thigh": np.array([0.1338, -0.0724, 0.3318]),
    "rl_thigh": np.array([-0.0864, 0.2594, 0.3318]),
    "rr_thigh": np.array([-0.0864, -0.0724, 0.3318]),
    "fl_calf": np.array([0.1510, 0.2669, 0.2174]),
    "fr_calf": np.array([0.1510, -0.0649, 0.2174]),
    "rl_calf": np.array([-0.1035, 0.2669, 0.2174]),
    "rr_calf": np.array([-0.1035, -0.0649, 0.2174]),
    "fl_foot": np.array([0.1672, 0.2112, 0.0776]),
    "fr_foot": np.array([0.1672, -0.1207, 0.0776]),
    "rl_foot": np.array([-0.1197, 0.2112, 0.0776]),
    "rr_foot": np.array([-0.1197, -0.1207, 0.0776]),
}
BODY_CENTER = np.array([0.0237, 0.1099, BASE_Z])

link_world_pos = {"base": BODY_CENTER}
for key, pos in SERVO_POS.items():
    link_world_pos[key] = pos

# ── STL I/O ──
def read_stl(path):
    with open(path, 'rb') as f:
        header = f.read(80)
        n = struct.unpack('<I', f.read(4))[0]
        triangles = []
        for _ in range(n):
            nx, ny, nz = struct.unpack('<fff', f.read(12))
            v1 = np.array(struct.unpack('<fff', f.read(12)))
            v2 = np.array(struct.unpack('<fff', f.read(12)))
            v3 = np.array(struct.unpack('<fff', f.read(12)))
            attr = struct.unpack('<H', f.read(2))[0]
            triangles.append((np.array([nx,ny,nz]), v1, v2, v3, attr))
    return header, triangles

def write_stl(path, header, triangles):
    with open(path, 'wb') as f:
        f.write(header)
        f.write(struct.pack('<I', len(triangles)))
        for normal, v1, v2, v3, attr in triangles:
            f.write(struct.pack('<fff', *normal))
            f.write(struct.pack('<fff', *v1))
            f.write(struct.pack('<fff', *v2))
            f.write(struct.pack('<fff', *v3))
            f.write(struct.pack('<H', attr))

def transform_stl(src, dst, offset):
    """Read STL, subtract offset from all vertices, write new STL."""
    header, triangles = read_stl(src)
    new_tris = []
    for normal, v1, v2, v3, attr in triangles:
        new_tris.append((normal, v1 - offset, v2 - offset, v3 - offset, attr))
    write_stl(dst, header, new_tris)

# ── Build mesh assignments ──
link_meshes = {"base": list(BODY_STLS)}
for leg in ["fl", "fr", "rl", "rr"]:
    for lt in ["hip", "thigh", "calf"]:
        link_meshes[f"{leg}_{lt}"] = []

for m in manifest:
    stl = m["stl"]
    name = m["name"]
    
    stl_key = stl.replace(".stl", "")
    if stl_key in SERVO_TO_LINK:
        leg, link_type = SERVO_TO_LINK[stl_key]
        if link_type == "base":
            link_meshes["base"].append(stl)
        else:
            link_meshes[f"{leg}_{link_type}"].append(stl)
        continue
    
    if stl in BODY_STLS:
        continue
    
    for part_type, link_type in PART_TO_LINK.items():
        if name.startswith(part_type):
            if part_type == "hip_cup":
                link_meshes["base"].append(stl)
                break
            
            if "servo_horn" in part_type:
                # Horn STL names: lower_leg_servo_horn_x2.stl, _001.stl, ..._007.stl
                clean = stl.replace(".stl", "")
                base_part = "lower_leg_servo_horn_x2"
                idx = clean.find(base_part)
                if idx >= 0:
                    suffix = clean[idx + len(base_part):]
                else:
                    suffix = ""
                leg = HORN_LEG.get(suffix, "rr")
            else:
                suffix = name[len(part_type):]
                if suffix.startswith("."):
                    suffix = suffix.replace(".", "_")
                leg = LEG_SUFFIX.get(suffix, "rr")
            
            if link_type == "base":
                link_meshes["base"].append(stl)
            else:
                link_meshes[f"{leg}_{link_type}"].append(stl)
            break

print("=== Mesh assignments ===")
for link in sorted(link_meshes.keys()):
    if link_meshes[link]:
        print(f"  {link}: {link_meshes[link]}")

# ── Transform all STLs to link-local coordinates ──
print("\n=== Transforming STLs to link-local coordinates ===")
for link_name, stls in link_meshes.items():
    wp = link_world_pos.get(link_name, BODY_CENTER)
    for stl in stls:
        src = os.path.join(MESH_SRC, stl)
        dst = os.path.join(MESH_DST, stl)
        if os.path.exists(src):
            transform_stl(src, dst, wp)
    print(f"  {link_name}: {len(stls)} meshes -> offset ({wp[0]:.4f}, {wp[1]:.4f}, {wp[2]:.4f})")

# ── Generate URDF ──
def visuals(stl_list):
    blocks = []
    for stl in stl_list:
        blocks.append(f"""    <visual>
      <origin xyz="0 0 0" rpy="0 0 0"/>
      <geometry><mesh filename="{MESH_REL}/{stl}"/></geometry>
    </visual>""")
    return "\n".join(blocks) if blocks else "    <!-- no visuals -->"

def make_leg(prefix):
    p = prefix.lower()
    
    hip_w = SERVO_POS[f"{p}_hip"]
    thigh_w = SERVO_POS[f"{p}_thigh"]
    calf_w = SERVO_POS[f"{p}_calf"]
    foot_w = SERVO_POS[f"{p}_foot"]
    
    hip_rel = hip_w - BODY_CENTER
    thigh_rel = thigh_w - hip_w
    calf_rel = calf_w - thigh_w
    foot_rel = foot_w - calf_w
    
    f4 = lambda v: f"{v[0]:.4f} {v[1]:.4f} {v[2]:.4f}"
    
    hip_vis = visuals(link_meshes.get(f"{p}_hip", []))
    thigh_vis = visuals(link_meshes.get(f"{p}_thigh", []))
    calf_vis = visuals(link_meshes.get(f"{p}_calf", []))
    
    return f"""
  <!-- {prefix.upper()} LEG -->
  <link name="{p}_hip">
{hip_vis}
    <collision><origin xyz="0 0 -0.05"/><geometry><cylinder radius="0.03" length="0.10"/></geometry></collision>
    <inertial><mass value="0.30"/><origin xyz="0 0 -0.05"/><inertia ixx="0.0001" ixy="0" ixz="0" iyy="0.0001" iyz="0" izz="0.00005"/></inertial>
  </link>
  <joint name="{p}_hip_joint" type="revolute">
    <parent link="base"/><child link="{p}_hip"/>
    <origin xyz="{f4(hip_rel)}"/><axis xyz="0 1 0"/>
    <limit lower="-0.78" upper="0.78" effort="20" velocity="5"/>
    <dynamics damping="0.5" friction="0.2"/>
  </joint>

  <link name="{p}_thigh">
{thigh_vis}
    <collision><origin xyz="0 0 -0.06"/><geometry><box size="0.025 0.02 0.12"/></geometry></collision>
    <inertial><mass value="0.15"/><origin xyz="0 0 -0.06"/><inertia ixx="0.0003" ixy="0" ixz="0" iyy="0.0003" iyz="0" izz="0.00003"/></inertial>
  </link>
  <joint name="{p}_thigh_joint" type="revolute">
    <parent link="{p}_hip"/><child link="{p}_thigh"/>
    <origin xyz="{f4(thigh_rel)}"/><axis xyz="1 0 0"/>
    <limit lower="-1.57" upper="1.57" effort="20" velocity="5"/>
    <dynamics damping="0.5" friction="0.2"/>
  </joint>

  <link name="{p}_calf">
{calf_vis}
    <collision><geometry><sphere radius="0.018"/></geometry></collision>
    <inertial><mass value="0.08"/><inertia ixx="0.0001" ixy="0" ixz="0" iyy="0.0001" iyz="0" izz="0.0001"/></inertial>
  </link>
  <joint name="{p}_knee_joint" type="revolute">
    <parent link="{p}_thigh"/><child link="{p}_calf"/>
    <origin xyz="{f4(calf_rel)}"/><axis xyz="1 0 0"/>
    <limit lower="-2.70" upper="0.5" effort="20" velocity="5"/>
    <dynamics damping="0.5" friction="0.2"/>
  </joint>

  <link name="{p}_foot">
    <collision><geometry><sphere radius="0.015"/></geometry></collision>
    <inertial><mass value="0.05"/><inertia ixx="0.00005" ixy="0" ixz="0" iyy="0.00005" iyz="0" izz="0.00005"/></inertial>
  </link>
  <joint name="{p}_foot_joint" type="fixed">
    <parent link="{p}_calf"/><child link="{p}_foot"/>
    <origin xyz="{f4(foot_rel)}"/>
  </joint>"""

body_vis = visuals(link_meshes["base"])

urdf = f"""<?xml version="1.0"?>
<robot name="quadruped">
  <link name="base">
{body_vis}
    <collision><geometry><box size="0.30 0.40 0.08"/></geometry></collision>
    <inertial><mass value="2.5"/><inertia ixx="0.008" ixy="0" ixz="0" iyy="0.015" iyz="0" izz="0.020"/></inertial>
  </link>
{make_leg("FL")}
{make_leg("FR")}
{make_leg("RL")}
{make_leg("RR")}
</robot>
"""

with open(URDF_PATH, 'w') as f:
    f.write(urdf)
print(f"\n[OK] Written: {URDF_PATH}")
print(f"[OK] Local meshes: {MESH_DST}")

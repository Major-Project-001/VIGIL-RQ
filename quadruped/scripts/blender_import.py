"""
blender_import.py — Import quadruped STL meshes into Blender 4.0 with joint hierarchy.

Usage:
  Open Blender → Scripting tab → Open this file → Run Script

Each joint is an Empty (arrows). Meshes are children of their joints.
Rotate/move meshes to align them, then run blender_export.py.
"""
import bpy
import os

# Clear scene
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()
for c in bpy.data.collections:
    if c.name != 'Collection':
        bpy.data.collections.remove(c)

# Find meshes directory
MESH_DIR = r"D:\Desktop\kutta\quadruped\urdf\meshes_centered"
if not os.path.isdir(MESH_DIR):
    raise FileNotFoundError(f"Not found: {MESH_DIR}")

SCALE = 0.001

COLORS = {
    "body":  (0.45, 0.45, 0.45, 1),
    "hip":   (0.2, 0.4, 0.8, 1),
    "thigh": (0.2, 0.7, 0.3, 1),
    "calf":  (0.9, 0.5, 0.1, 1),
    "foot":  (0.15, 0.15, 0.15, 1),
}

def make_mat(name, rgba):
    mat = bpy.data.materials.get(name)
    if not mat:
        mat = bpy.data.materials.new(name)
        mat.use_nodes = True
        bsdf = mat.node_tree.nodes.get("Principled BSDF")
        if bsdf:
            bsdf.inputs[0].default_value = rgba
    return mat

for n, c in COLORS.items():
    make_mat(n, c)

def add_stl(stl_name, obj_name, parent, mat_name, loc=(0,0,0)):
    path = os.path.join(MESH_DIR, stl_name)
    if not os.path.exists(path):
        print(f"SKIP: {path}")
        return None
    bpy.ops.wm.stl_import(filepath=path)
    obj = bpy.context.active_object
    obj.name = obj_name
    # Make mesh single-user (avoids error when same STL imported multiple times)
    obj.data = obj.data.copy()
    obj.scale = (SCALE, SCALE, SCALE)
    bpy.ops.object.transform_apply(scale=True)
    obj.location = loc
    mat = bpy.data.materials.get(mat_name)
    if mat:
        obj.data.materials.clear()
        obj.data.materials.append(mat)
    obj.parent = parent
    return obj

def add_empty(name, loc, parent=None):
    e = bpy.data.objects.new(name, None)
    bpy.context.collection.objects.link(e)
    e.empty_display_type = 'ARROWS'
    e.empty_display_size = 0.03
    e.location = loc
    if parent:
        e.parent = parent
    return e

# ── BASE BODY ──
base = add_empty("BASE", (0, 0, 0.45))

# Body parts (group-recentered, keep relative positions)
add_stl("side_x2.stl", "body__side_L", base, "body")
obj = add_stl("side_x2.stl", "body__side_R", base, "body")
if obj: obj.scale.x = -1
add_stl("middle.stl", "body__middle", base, "body")
add_stl("horizontal_x4.stl", "body__horiz_L", base, "body")
obj = add_stl("horizontal_x4.stl", "body__horiz_R", base, "body")
if obj: obj.scale.x = -1
add_stl("legs_middle_x2.stl", "body__legsmid_L", base, "body")
obj = add_stl("legs_middle_x2.stl", "body__legsmid_R", base, "body")
if obj: obj.scale.x = -1

# ── LEGS ──
legs = {
    "FL": (0.117, 0.068, 0),
    "FR": (0.117, -0.068, 0),
    "RL": (-0.117, 0.068, 0),
    "RR": (-0.117, -0.068, 0),
}

for leg, hip_pos in legs.items():
    hip = add_empty(f"{leg}_hip_joint", hip_pos, base)
    for s in ["hip_1.stl","hip_2.stl","hip_cup.stl","hip_servo_gear.stl"]:
        add_stl(s, f"{leg}__{s[:-4]}", hip, "hip")
    
    thigh = add_empty(f"{leg}_thigh_joint", (0,0,-0.09), hip)
    for s in ["upper_leg_x2.stl","servo_frame_1.stl"]:
        add_stl(s, f"{leg}__{s[:-4]}", thigh, "thigh", loc=(0,0,-0.075))
    
    knee = add_empty(f"{leg}_knee_joint", (0,0,-0.15), thigh)
    for s in ["lower_leg.stl","lower_leg_servo_horn_x2.stl"]:
        add_stl(s, f"{leg}__{s[:-4]}", knee, "calf", loc=(0,0,-0.075))
    
    foot = add_empty(f"{leg}_foot_joint", (0,0,-0.15), knee)
    add_stl("foot.stl", f"{leg}__foot", foot, "foot")

# ── Ground plane ──
bpy.ops.mesh.primitive_plane_add(size=2, location=(0,0,0))
bpy.context.active_object.name = "Ground"

print("\n" + "="*50)
print("  IMPORTED! Adjust mesh rotations/positions,")
print("  then run blender_export.py")
print("="*50)

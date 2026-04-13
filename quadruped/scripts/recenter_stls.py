"""
recenter_stls.py — Recenter STL files intelligently:
  - BODY parts: offset by a common assembly center (preserves relative positions)
  - LEG/FOOT parts: each centered individually at origin
"""
import struct
import os

def read_stl_binary(filepath):
    triangles = []
    with open(filepath, 'rb') as f:
        header = f.read(80)
        num_tri = struct.unpack('<I', f.read(4))[0]
        for _ in range(num_tri):
            nx, ny, nz = struct.unpack('<fff', f.read(12))
            v1 = struct.unpack('<fff', f.read(12))
            v2 = struct.unpack('<fff', f.read(12))
            v3 = struct.unpack('<fff', f.read(12))
            attr = struct.unpack('<H', f.read(2))[0]
            triangles.append(((nx,ny,nz), v1, v2, v3, attr))
    return header, triangles

def write_stl_binary(filepath, header, triangles):
    with open(filepath, 'wb') as f:
        f.write(header)
        f.write(struct.pack('<I', len(triangles)))
        for normal, v1, v2, v3, attr in triangles:
            f.write(struct.pack('<fff', *normal))
            f.write(struct.pack('<fff', *v1))
            f.write(struct.pack('<fff', *v2))
            f.write(struct.pack('<fff', *v3))
            f.write(struct.pack('<H', attr))

def get_all_verts(triangles):
    verts = []
    for _, v1, v2, v3, _ in triangles:
        verts.extend([v1, v2, v3])
    return verts

def get_bbox(verts):
    xs = [v[0] for v in verts]
    ys = [v[1] for v in verts]
    zs = [v[2] for v in verts]
    return (min(xs), min(ys), min(zs)), (max(xs), max(ys), max(zs))

def shift_triangles(triangles, dx, dy, dz):
    result = []
    for normal, v1, v2, v3, attr in triangles:
        result.append((normal,
            (v1[0]+dx, v1[1]+dy, v1[2]+dz),
            (v2[0]+dx, v2[1]+dy, v2[2]+dz),
            (v3[0]+dx, v3[1]+dy, v3[2]+dz), attr))
    return result

script_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(script_dir, "..", "urdf", "meshes")
dst_dir = os.path.join(script_dir, "..", "urdf", "meshes_centered")
os.makedirs(dst_dir, exist_ok=True)

# Define groups
BODY_PARTS = ['middle.stl', 'side_x2.stl', 'horizontal_x4.stl', 'legs_middle_x2.stl']
LEG_PARTS = ['hip_1.stl', 'hip_2.stl', 'hip_cup.stl', 'hip_servo_gear.stl',
             'upper_leg_x2.stl', 'servo_frame_1.stl', 'servo_frame_2.stl',
             'lower_leg.stl', 'lower_leg_servo_horn_x2.stl', 'foot.stl']
ELECTRONICS = ['PI4_up.stl', 'PI4_down.stl', 'ESC_up.stl', 'ESC_down.stl',
               'battery_support_1.stl', 'battery_support_2.stl', 'realsense_adapter.stl']

# Step 1: Compute combined bounding box center for ALL body parts
print("=== BODY PARTS (group-centered) ===")
all_body_verts = []
body_data = {}
for fname in BODY_PARTS:
    path = os.path.join(src_dir, fname)
    header, tris = read_stl_binary(path)
    body_data[fname] = (header, tris)
    all_body_verts.extend(get_all_verts(tris))

(bmin_x, bmin_y, bmin_z), (bmax_x, bmax_y, bmax_z) = get_bbox(all_body_verts)
body_cx = (bmin_x + bmax_x) / 2
body_cy = (bmin_y + bmax_y) / 2
body_cz = (bmin_z + bmax_z) / 2
print(f"  Body assembly bbox: ({bmin_x:.1f},{bmin_y:.1f},{bmin_z:.1f}) to ({bmax_x:.1f},{bmax_y:.1f},{bmax_z:.1f})")
print(f"  Body assembly center: ({body_cx:.1f}, {body_cy:.1f}, {body_cz:.1f})")

for fname in BODY_PARTS:
    header, tris = body_data[fname]
    tris_shifted = shift_triangles(tris, -body_cx, -body_cy, -body_cz)
    dst = os.path.join(dst_dir, fname)
    write_stl_binary(dst, header, tris_shifted)
    print(f"  {fname:<35} shifted by ({-body_cx:.1f}, {-body_cy:.1f}, {-body_cz:.1f})")

# Step 2: Center each leg part individually
print("\n=== LEG PARTS (individually centered) ===")
for fname in LEG_PARTS:
    path = os.path.join(src_dir, fname)
    if not os.path.exists(path):
        continue
    header, tris = read_stl_binary(path)
    verts = get_all_verts(tris)
    (mn_x, mn_y, mn_z), (mx_x, mx_y, mx_z) = get_bbox(verts)
    cx = (mn_x + mx_x) / 2
    cy = (mn_y + mx_y) / 2
    cz = (mn_z + mx_z) / 2
    tris_shifted = shift_triangles(tris, -cx, -cy, -cz)
    dst = os.path.join(dst_dir, fname)
    write_stl_binary(dst, header, tris_shifted)
    print(f"  {fname:<35} center=({cx:.1f}, {cy:.1f}, {cz:.1f}) → (0,0,0)")

# Step 3: Electronics (individually centered, for completeness)
print("\n=== ELECTRONICS (individually centered) ===")
for fname in ELECTRONICS:
    path = os.path.join(src_dir, fname)
    if not os.path.exists(path):
        continue
    header, tris = read_stl_binary(path)
    verts = get_all_verts(tris)
    (mn_x, mn_y, mn_z), (mx_x, mx_y, mx_z) = get_bbox(verts)
    cx = (mn_x + mx_x) / 2
    cy = (mn_y + mx_y) / 2
    cz = (mn_z + mx_z) / 2
    tris_shifted = shift_triangles(tris, -cx, -cy, -cz)
    dst = os.path.join(dst_dir, fname)
    write_stl_binary(dst, header, tris_shifted)
    print(f"  {fname:<35} center=({cx:.1f}, {cy:.1f}, {cz:.1f}) → (0,0,0)")

print(f"\nDone. Output: {dst_dir}")

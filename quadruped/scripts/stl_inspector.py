"""
stl_inspector.py — Detailed STL analysis: bounding box, centroid, axis alignment.
Reports dimensions and suggests rotations for URDF integration.
"""
import struct
import os

def read_stl_binary(filepath):
    """Read binary STL and return list of vertex coordinates."""
    vertices = []
    with open(filepath, 'rb') as f:
        header = f.read(80)
        num_triangles = struct.unpack('<I', f.read(4))[0]
        for _ in range(num_triangles):
            f.read(12)  # normal vector
            for _ in range(3):
                x, y, z = struct.unpack('<fff', f.read(12))
                vertices.append((x, y, z))
            f.read(2)  # attribute byte count
    return vertices

def analyze_stl(filepath):
    """Return detailed bounding box and centroid info."""
    verts = read_stl_binary(filepath)
    xs = [v[0] for v in verts]
    ys = [v[1] for v in verts]
    zs = [v[2] for v in verts]
    
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    min_z, max_z = min(zs), max(zs)
    
    size_x = max_x - min_x
    size_y = max_y - min_y
    size_z = max_z - min_z
    
    # Centroid (geometric center of bbox)
    cx = (min_x + max_x) / 2
    cy = (min_y + max_y) / 2
    cz = (min_z + max_z) / 2
    
    return {
        'min': (min_x, min_y, min_z),
        'max': (max_x, max_y, max_z),
        'size': (size_x, size_y, size_z),
        'center': (cx, cy, cz),
        'longest_axis': ['X', 'Y', 'Z'][[size_x, size_y, size_z].index(max(size_x, size_y, size_z))],
    }

meshes_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "urdf", "meshes")

print("=" * 100)
print("STL MESH ANALYSIS — All dimensions in mm (STL native units)")
print("=" * 100)

categories = {
    'BODY': ['middle.stl', 'side_x2.stl', 'horizontal_x4.stl', 'legs_middle_x2.stl'],
    'HIP': ['hip_1.stl', 'hip_2.stl', 'hip_cup.stl', 'hip_servo_gear.stl'],
    'UPPER LEG': ['upper_leg_x2.stl', 'servo_frame_1.stl', 'servo_frame_2.stl'],
    'LOWER LEG': ['lower_leg.stl', 'lower_leg_servo_horn_x2.stl'],
    'FOOT': ['foot.stl'],
    'ELECTRONICS': ['PI4_up.stl', 'PI4_down.stl', 'ESC_up.stl', 'ESC_down.stl',
                    'battery_support_1.stl', 'battery_support_2.stl', 'realsense_adapter.stl'],
}

for category, files in categories.items():
    print(f"\n--- {category} ---")
    print(f"{'File':<32} {'SizeX':>7} {'SizeY':>7} {'SizeZ':>7}  "
          f"{'CenterX':>8} {'CenterY':>8} {'CenterZ':>8}  {'Long':>4}")
    for f in files:
        path = os.path.join(meshes_dir, f)
        if not os.path.exists(path):
            print(f"{f:<32} NOT FOUND")
            continue
        info = analyze_stl(path)
        s = info['size']
        c = info['center']
        print(f"{f:<32} {s[0]:>7.1f} {s[1]:>7.1f} {s[2]:>7.1f}  "
              f"{c[0]:>8.1f} {c[1]:>8.1f} {c[2]:>8.1f}  {info['longest_axis']:>4}")
        # Also print min/max
        mn = info['min']
        mx = info['max']
        print(f"{'':>32}   min=({mn[0]:.1f}, {mn[1]:.1f}, {mn[2]:.1f})  "
              f"max=({mx[0]:.1f}, {mx[1]:.1f}, {mx[2]:.1f})")

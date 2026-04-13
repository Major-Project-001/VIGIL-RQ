"""Compute joint positions from exported servo STL centroids."""
import struct
import os
import json
import numpy as np

MESH_DIR = r"D:\Desktop\kutta\quadruped\urdf\meshes_export"
CONFIG_DIR = r"D:\Desktop\kutta\quadruped\config"

with open(os.path.join(CONFIG_DIR, "export_manifest.json")) as f:
    manifest = json.load(f)

def stl_centroid(filepath):
    """Read binary STL and return centroid of all triangle vertices."""
    with open(filepath, 'rb') as f:
        f.read(80)  # header
        n_tri = struct.unpack('<I', f.read(4))[0]
        verts = []
        for _ in range(n_tri):
            f.read(12)  # normal
            for _ in range(3):
                v = struct.unpack('<fff', f.read(12))
                verts.append(v)
            f.read(2)  # attribute
    verts = np.array(verts)
    return verts.mean(axis=0), verts.min(axis=0), verts.max(axis=0)

print("=== SERVO POSITIONS (world space centroids) ===\n")

# Analyze all servo meshes
servos = []
for m in manifest:
    if "Servo" in m["name"] or "29KG" in m["name"]:
        path = os.path.join(MESH_DIR, m["stl"])
        cent, vmin, vmax = stl_centroid(path)
        dims = vmax - vmin
        servos.append({"name": m["name"], "stl": m["stl"], "centroid": cent, 
                       "dims": dims, "min": vmin, "max": vmax})
        print(f"  {m['name']:<35} center=({cent[0]:.4f}, {cent[1]:.4f}, {cent[2]:.4f})  "
              f"dims=({dims[0]*1000:.0f}x{dims[1]*1000:.0f}x{dims[2]*1000:.0f}mm)")

# Also analyze hip servo gears
print("\n=== HIP SERVO GEAR POSITIONS ===\n")
for m in manifest:
    if "hip_servo_gear" in m["name"]:
        path = os.path.join(MESH_DIR, m["stl"])
        cent, vmin, vmax = stl_centroid(path)
        dims = vmax - vmin
        print(f"  {m['name']:<35} center=({cent[0]:.4f}, {cent[1]:.4f}, {cent[2]:.4f})  "
              f"dims=({dims[0]*1000:.0f}x{dims[1]*1000:.0f}x{dims[2]*1000:.0f}mm)")

# Hip servo cup positions
print("\n=== HIP CUP POSITIONS ===\n") 
for m in manifest:
    if "hip_cup" in m["name"]:
        path = os.path.join(MESH_DIR, m["stl"])
        cent, vmin, vmax = stl_centroid(path)
        dims = vmax - vmin
        print(f"  {m['name']:<35} center=({cent[0]:.4f}, {cent[1]:.4f}, {cent[2]:.4f})  "
              f"dims=({dims[0]*1000:.0f}x{dims[1]*1000:.0f}x{dims[2]*1000:.0f}mm)")

# hip_1 positions  
print("\n=== HIP_1 POSITIONS ===\n")
for m in manifest:
    if m["name"].startswith("hip_1"):
        path = os.path.join(MESH_DIR, m["stl"])
        cent, vmin, vmax = stl_centroid(path)
        dims = vmax - vmin
        print(f"  {m['name']:<35} center=({cent[0]:.4f}, {cent[1]:.4f}, {cent[2]:.4f})  "
              f"dims=({dims[0]*1000:.0f}x{dims[1]*1000:.0f}x{dims[2]*1000:.0f}mm)")

# hip_2 positions
print("\n=== HIP_2 POSITIONS ===\n")
for m in manifest:
    if "hip_2" in m["name"]:
        path = os.path.join(MESH_DIR, m["stl"])
        cent, vmin, vmax = stl_centroid(path)
        dims = vmax - vmin
        print(f"  {m['name']:<35} center=({cent[0]:.4f}, {cent[1]:.4f}, {cent[2]:.4f})  "
              f"dims=({dims[0]*1000:.0f}x{dims[1]*1000:.0f}x{dims[2]*1000:.0f}mm)")

# upper_leg positions
print("\n=== UPPER LEG POSITIONS ===\n")
for m in manifest:
    if "upper_leg" in m["name"]:
        path = os.path.join(MESH_DIR, m["stl"])
        cent, vmin, vmax = stl_centroid(path)
        dims = vmax - vmin
        print(f"  {m['name']:<35} center=({cent[0]:.4f}, {cent[1]:.4f}, {cent[2]:.4f})  "
              f"dims=({dims[0]*1000:.0f}x{dims[1]*1000:.0f}x{dims[2]*1000:.0f}mm)")

# lower_leg positions
print("\n=== LOWER LEG POSITIONS ===\n")  
for m in manifest:
    if "lower_leg" in m["name"] and "servo" not in m["name"]:
        path = os.path.join(MESH_DIR, m["stl"])
        cent, vmin, vmax = stl_centroid(path)
        dims = vmax - vmin
        print(f"  {m['name']:<35} center=({cent[0]:.4f}, {cent[1]:.4f}, {cent[2]:.4f})  "
              f"dims=({dims[0]*1000:.0f}x{dims[1]*1000:.0f}x{dims[2]*1000:.0f}mm)")

# foot positions
print("\n=== FOOT POSITIONS ===\n")
for m in manifest:
    if "foot" in m["name"]:
        path = os.path.join(MESH_DIR, m["stl"])
        cent, vmin, vmax = stl_centroid(path)
        dims = vmax - vmin
        print(f"  {m['name']:<35} center=({cent[0]:.4f}, {cent[1]:.4f}, {cent[2]:.4f})  "
              f"dims=({dims[0]*1000:.0f}x{dims[1]*1000:.0f}x{dims[2]*1000:.0f}mm)")

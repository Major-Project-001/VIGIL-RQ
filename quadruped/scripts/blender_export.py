"""
blender_export.py — Export mesh transforms from Blender to JSON for URDF generation.

Usage:
  1. After aligning meshes in Blender (from blender_import.py)
  2. Go to Scripting tab
  3. Open this file and click Run Script
  4. It saves transforms to quadruped/config/mesh_transforms.json
  5. Then run: python quadruped/scripts/build_urdf.py
"""
import bpy
import json
import os
import math
import mathutils

output_path = r"D:\Desktop\kutta\quadruped\config\mesh_transforms.json"
os.makedirs(os.path.dirname(output_path), exist_ok=True)

transforms = {}

for obj in bpy.data.objects:
    if obj.type != 'MESH':
        continue
    if obj.name in ['Ground']:
        continue
    
    # Get local transform relative to parent
    loc = obj.location.copy()
    rot = obj.rotation_euler.copy()
    scl = obj.scale.copy()
    
    # Determine which link/part this belongs to
    name = obj.name
    
    transforms[name] = {
        "location": [round(loc.x, 6), round(loc.y, 6), round(loc.z, 6)],
        "rotation_euler": [round(rot.x, 6), round(rot.y, 6), round(rot.z, 6)],
        "scale": [round(scl.x, 6), round(scl.y, 6), round(scl.z, 6)],
        "parent": obj.parent.name if obj.parent else None,
    }

with open(output_path, 'w') as f:
    json.dump(transforms, f, indent=2)

print(f"\nExported {len(transforms)} mesh transforms to:")
print(f"  {output_path}")
print("\nNow run: python quadruped/scripts/build_urdf.py")

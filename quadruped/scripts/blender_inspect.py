"""
blender_inspect.py — Run inside Blender to inspect scene hierarchy and export info.
Prints all objects, their types, parents, locations, rotations.

Usage: Open full.blend in Blender, go to Scripting tab, open+run this file.
       Output appears in Blender's System Console (Window→Toggle System Console)
       AND saves to D:\Desktop\kutta\quadruped\config\scene_info.json
"""
import bpy
import json
import os

output = {}
print("\n" + "="*80)
print("BLENDER SCENE INSPECTOR")
print("="*80)

for obj in sorted(bpy.data.objects, key=lambda o: o.name):
    info = {
        "type": obj.type,
        "location": [round(x, 6) for x in obj.location],
        "rotation_euler": [round(x, 6) for x in obj.rotation_euler],
        "scale": [round(x, 6) for x in obj.scale],
        "parent": obj.parent.name if obj.parent else None,
        "children": [c.name for c in obj.children],
    }
    if obj.type == 'MESH':
        info["vertex_count"] = len(obj.data.vertices)
        info["dimensions"] = [round(x, 6) for x in obj.dimensions]
    
    output[obj.name] = info
    
    parent_str = f" → parent: {obj.parent.name}" if obj.parent else ""
    print(f"  {obj.name:<40} type={obj.type:<8} loc=({info['location'][0]:.3f}, {info['location'][1]:.3f}, {info['location'][2]:.3f}){parent_str}")

# Save to JSON
out_path = r"D:\Desktop\kutta\quadruped\config\scene_info.json"
os.makedirs(os.path.dirname(out_path), exist_ok=True)
with open(out_path, 'w') as f:
    json.dump(output, f, indent=2)

print(f"\nSaved scene info to: {out_path}")
print(f"Total objects: {len(output)}")
print("="*80)

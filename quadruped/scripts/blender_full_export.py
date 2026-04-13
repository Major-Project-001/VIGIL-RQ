"""
blender_full_export.py - Export the completed Blender model for PyBullet.

Reads scene hierarchy, exports meshes as STL, saves scene info JSON.

Usage: Open full.blend -> Scripting tab -> Open this file -> Run Script
"""
import bpy
import os
import json
import math
import mathutils

# ── Output paths ──
BASE_DIR = r"D:\Desktop\kutta\quadruped"
EXPORT_MESH_DIR = os.path.join(BASE_DIR, "urdf", "meshes_export")
URDF_PATH = os.path.join(BASE_DIR, "urdf", "robot.urdf")
CONFIG_DIR = os.path.join(BASE_DIR, "config")
os.makedirs(EXPORT_MESH_DIR, exist_ok=True)
os.makedirs(CONFIG_DIR, exist_ok=True)

# ── Step 1: Inspect and save scene hierarchy ──
scene_data = {}
print("\n" + "="*70)
print("  BLENDER -> PYBULLET EXPORTER")
print("="*70)
print("\nScene objects:")

for obj in sorted(bpy.data.objects, key=lambda o: o.name):
    info = {
        "type": obj.type,
        "location": [round(x, 6) for x in obj.location],
        "rotation_euler": [round(x, 6) for x in obj.rotation_euler],
        "rotation_mode": obj.rotation_mode,
        "scale": [round(x, 6) for x in obj.scale],
        "parent": obj.parent.name if obj.parent else None,
        "children": [c.name for c in obj.children],
    }
    if obj.type == 'MESH':
        info["vertex_count"] = len(obj.data.vertices)
        info["dimensions"] = [round(x*1000, 1) for x in obj.dimensions]  # mm
    scene_data[obj.name] = info
    
    p = f" -> {obj.parent.name}" if obj.parent else ""
    dim = ""
    if obj.type == 'MESH':
        d = info["dimensions"]
        dim = f" [{d[0]:.0f}x{d[1]:.0f}x{d[2]:.0f}mm]"
    print(f"  {obj.name:<40} {obj.type:<8}{dim}{p}")

with open(os.path.join(CONFIG_DIR, "scene_info.json"), 'w') as f:
    json.dump(scene_data, f, indent=2)

print(f"\nTotal: {len(scene_data)} objects")
print(f"Scene info saved to: {os.path.join(CONFIG_DIR, 'scene_info.json')}")

# ── Step 2: Export each mesh object as individual STL ──
print("\nExporting meshes...")
exported = []

for obj in bpy.data.objects:
    if obj.type != 'MESH':
        continue
    if obj.name in ['Ground']:
        continue
    
    # Select only this object
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    
    # Export with transforms applied
    stl_name = obj.name.replace(" ", "_").replace(".", "_") + ".stl"
    stl_path = os.path.join(EXPORT_MESH_DIR, stl_name)
    
    # Use the STL exporter (Blender 4.0 API)
    bpy.ops.export_mesh.stl(
        filepath=stl_path,
        use_selection=True,
        global_scale=1.0,
        use_mesh_modifiers=True,
        ascii=False,
    )
    
    exported.append({
        "name": obj.name,
        "stl": stl_name,
        "parent": obj.parent.name if obj.parent else None,
        "location": [round(x, 6) for x in obj.location],
        "rotation": [round(x, 6) for x in obj.rotation_euler],
        "scale": [round(x, 6) for x in obj.scale],
    })
    print(f"  Exported: {stl_name}")

# Save export manifest
with open(os.path.join(CONFIG_DIR, "export_manifest.json"), 'w') as f:
    json.dump(exported, f, indent=2)

print(f"\nExported {len(exported)} meshes to: {EXPORT_MESH_DIR}")
print(f"Manifest: {os.path.join(CONFIG_DIR, 'export_manifest.json')}")

print("\n" + "="*70)
print("  EXPORT COMPLETE!")
print("  Next: Run 'python quadruped/scripts/build_urdf.py' to generate URDF")
print("="*70)

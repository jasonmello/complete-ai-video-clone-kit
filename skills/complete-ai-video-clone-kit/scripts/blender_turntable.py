"""Stage 3 (3D): 360° turntable of a 3D model rendered to transparent PNGs (headless Blender).

usage: blender -b -P blender_turntable.py -- model.glb out_dir [seconds=4] [fps=30] [width=1080] [height=1920]
then:  ffmpeg -framerate 30 -i out_dir/%04d.png -c:v libx264 -pix_fmt yuv420p turntable.mp4
"""
import bpy, sys, math, os
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
if len(argv) < 2:
    sys.exit(__doc__)
model, out_dir = argv[0], argv[1]
secs, fps = float(argv[2]) if len(argv) > 2 else 4, int(argv[3]) if len(argv) > 3 else 30
W, H = int(argv[4]) if len(argv) > 4 else 1080, int(argv[5]) if len(argv) > 5 else 1920

bpy.ops.wm.read_factory_settings(use_empty=True)
ext = os.path.splitext(model)[1].lower()
{".glb": bpy.ops.import_scene.gltf, ".gltf": bpy.ops.import_scene.gltf,
 ".fbx": bpy.ops.import_scene.fbx, ".obj": bpy.ops.wm.obj_import}[ext](filepath=model)

objs = [o for o in bpy.context.scene.objects if o.type == "MESH"]
pts = [o.matrix_world @ Vector(c) for o in objs for c in o.bound_box]
lo = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
hi = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
center, radius = (lo + hi) / 2, (hi - lo).length / 2

pivot = bpy.data.objects.new("pivot", None); bpy.context.scene.collection.objects.link(pivot); pivot.location = center
cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam")); bpy.context.scene.collection.objects.link(cam)
cam.parent = pivot; cam.location = (0, -radius * 3.2, radius * 0.6)
trk = cam.constraints.new("TRACK_TO"); trk.target = pivot; trk.track_axis = "TRACK_NEGATIVE_Z"; trk.up_axis = "UP_Y"
bpy.context.scene.camera = cam
for rot, energy in (((50, 0, 30), 4), ((60, 0, 210), 1.5)):
    light = bpy.data.objects.new("sun", bpy.data.lights.new("sun", "SUN")); light.data.energy = energy
    light.rotation_euler = [math.radians(v) for v in rot]; bpy.context.scene.collection.objects.link(light)

sc = bpy.context.scene
n = int(secs * fps)
sc.frame_start, sc.frame_end, sc.render.fps = 1, n, fps
pivot.rotation_euler = (0, 0, 0); pivot.keyframe_insert("rotation_euler", frame=1)
pivot.rotation_euler = (0, 0, math.radians(360)); pivot.keyframe_insert("rotation_euler", frame=n + 1)
for fc in pivot.animation_data.action.fcurves:
    for k in fc.keyframe_points:
        k.interpolation = "LINEAR"
engines = [e.identifier for e in bpy.types.RenderSettings.bl_rna.properties["engine"].enum_items]
sc.render.engine = "BLENDER_EEVEE_NEXT" if "BLENDER_EEVEE_NEXT" in engines else "BLENDER_EEVEE"
sc.render.resolution_x, sc.render.resolution_y = W, H
sc.render.film_transparent = True
sc.render.image_settings.file_format = "PNG"; sc.render.image_settings.color_mode = "RGBA"
sc.render.filepath = os.path.join(os.path.abspath(out_dir), "")
bpy.ops.render.render(animation=True)
print("ok →", out_dir)

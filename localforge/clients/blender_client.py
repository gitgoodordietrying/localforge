"""
Blender automation client.

Runs Blender in headless mode to generate 3D models, render scenes,
create textures, and export to various formats.
"""

import os
import platform
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Dict, Optional

from ..engine.config import get_config


def _find_blender() -> Optional[str]:
    """Find Blender executable."""
    config = get_config()
    configured = config.blender_path
    if configured and Path(configured).exists():
        return configured

    found = shutil.which("blender")
    if found:
        return found

    system = platform.system()
    candidates = []
    if system == "Windows":
        pf = Path(os.environ.get("ProgramFiles", "C:\\Program Files")) / "Blender Foundation"
        if pf.exists():
            for d in sorted(pf.iterdir(), reverse=True):
                exe = d / "blender.exe"
                if exe.exists():
                    candidates.append(str(exe))
    elif system == "Darwin":
        candidates.append("/Applications/Blender.app/Contents/MacOS/Blender")
    else:
        candidates.extend(["/usr/bin/blender", "/snap/bin/blender"])

    for c in candidates:
        if Path(c).exists():
            return c
    return None


class BlenderClient:
    """Client for automating Blender operations."""

    def __init__(self, blender_path: Path = None):
        path = str(blender_path) if blender_path else _find_blender()
        if not path or not Path(path).exists():
            raise RuntimeError(
                "Blender not found. Set services.blender.path in localforge.yaml"
            )
        self.blender_path = Path(path)

    def get_version(self) -> str:
        """Get Blender version."""
        result = subprocess.run(
            [str(self.blender_path), "--version"],
            capture_output=True, text=True, timeout=30,
        )
        return result.stdout.strip().split("\n")[0]

    def run_script(self, script_content: str, blend_file: Path = None,
                   timeout: int = 300) -> Dict[str, Any]:
        """Run a Python script in Blender headlessly."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(script_content)
            script_path = f.name

        try:
            cmd = [str(self.blender_path), "--background"]
            if blend_file:
                cmd.append(str(blend_file))
            cmd.extend(["--python", script_path])

            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=timeout
            )
            return {
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "return_code": result.returncode,
            }
        finally:
            Path(script_path).unlink(missing_ok=True)

    def render_scene(self, blend_file: Path, output_path: Path,
                     resolution: tuple = (1920, 1080),
                     samples: int = 128) -> Path:
        """Render a .blend file to an image."""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        script = f'''
import bpy
bpy.context.scene.render.resolution_x = {resolution[0]}
bpy.context.scene.render.resolution_y = {resolution[1]}
bpy.context.scene.render.image_settings.file_format = 'PNG'
bpy.context.scene.render.filepath = r"{output_path}"
if hasattr(bpy.context.scene, 'eevee'):
    bpy.context.scene.eevee.taa_render_samples = {samples}
if hasattr(bpy.context.scene, 'cycles'):
    bpy.context.scene.cycles.samples = {samples}
bpy.ops.render.render(write_still=True)
'''
        result = self.run_script(script, blend_file)
        if not result["success"]:
            raise RuntimeError(f"Render failed: {result['stderr']}")
        return output_path

    def render_animation(self, blend_file: Path, output_dir: Path,
                         frame_start: int = 1, frame_end: int = 24,
                         resolution: tuple = (1920, 1080)) -> Path:
        """Render an animation from a .blend file."""
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        script = f'''
import bpy
bpy.context.scene.render.resolution_x = {resolution[0]}
bpy.context.scene.render.resolution_y = {resolution[1]}
bpy.context.scene.render.image_settings.file_format = 'PNG'
bpy.context.scene.render.filepath = r"{output_dir}/frame_"
bpy.context.scene.frame_start = {frame_start}
bpy.context.scene.frame_end = {frame_end}
bpy.ops.render.render(animation=True)
'''
        result = self.run_script(script, blend_file)
        if not result["success"]:
            raise RuntimeError(f"Animation render failed: {result['stderr']}")
        return output_dir

    def create_primitive(self, shape: str, output_path: Path,
                         size: float = 1.0, subdivisions: int = 2) -> Path:
        """Create a primitive 3D shape and export it."""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        ext = output_path.suffix.lower()

        shape_ops = {
            "cube": f"bpy.ops.mesh.primitive_cube_add(size={size})",
            "sphere": f"bpy.ops.mesh.primitive_uv_sphere_add(radius={size/2}, segments=32, ring_count=16)",
            "cylinder": f"bpy.ops.mesh.primitive_cylinder_add(radius={size/2}, depth={size})",
            "cone": f"bpy.ops.mesh.primitive_cone_add(radius1={size/2}, depth={size})",
            "torus": f"bpy.ops.mesh.primitive_torus_add(major_radius={size/2}, minor_radius={size/4})",
            "plane": f"bpy.ops.mesh.primitive_plane_add(size={size})",
        }

        if shape not in shape_ops:
            raise ValueError(f"Unknown shape: {shape}. Options: {list(shape_ops.keys())}")

        export_ops = {
            ".glb": f'bpy.ops.export_scene.gltf(filepath=r"{output_path}", export_format="GLB")',
            ".gltf": f'bpy.ops.export_scene.gltf(filepath=r"{output_path}", export_format="GLTF_SEPARATE")',
            ".fbx": f'bpy.ops.export_scene.fbx(filepath=r"{output_path}")',
            ".obj": f'bpy.ops.wm.obj_export(filepath=r"{output_path}")',
        }

        if ext not in export_ops:
            raise ValueError(f"Unsupported export format: {ext}")

        script = f'''
import bpy
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()
{shape_ops[shape]}
if {subdivisions} > 0:
    bpy.ops.object.modifier_add(type='SUBSURF')
    bpy.context.object.modifiers["Subdivision"].levels = {subdivisions}
    bpy.ops.object.modifier_apply(modifier="Subdivision")
bpy.ops.object.shade_smooth()
{export_ops[ext]}
'''
        result = self.run_script(script)
        if not result["success"]:
            raise RuntimeError(f"Primitive creation failed: {result['stderr']}")
        return output_path

    def create_text_3d(self, text: str, output_path: Path,
                       font_size: float = 1.0, extrude: float = 0.1) -> Path:
        """Create 3D text and export it."""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        script = f'''
import bpy
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()
bpy.ops.object.text_add()
text_obj = bpy.context.object
text_obj.data.body = "{text}"
text_obj.data.size = {font_size}
text_obj.data.extrude = {extrude}
bpy.ops.object.convert(target='MESH')
bpy.ops.object.origin_set(type='ORIGIN_CENTER_OF_MASS')
bpy.ops.export_scene.gltf(filepath=r"{output_path}", export_format="GLB")
'''
        result = self.run_script(script)
        if not result["success"]:
            raise RuntimeError(f"3D text creation failed: {result['stderr']}")
        return output_path

    def generate_procedural_texture(self, texture_type: str, output_path: Path,
                                    resolution: int = 1024) -> Path:
        """Generate a procedural texture image."""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        texture_nodes = {
            "noise": "ShaderNodeTexNoise",
            "clouds": "ShaderNodeTexMusgrave",
            "marble": "ShaderNodeTexWave",
            "wood": "ShaderNodeTexWave",
            "brick": "ShaderNodeTexBrick",
        }

        if texture_type not in texture_nodes:
            raise ValueError(f"Unknown texture type: {texture_type}")

        script = f'''
import bpy
mat = bpy.data.materials.new("ProceduralMat")
mat.use_nodes = True
nodes = mat.node_tree.nodes
links = mat.node_tree.links
for node in nodes:
    nodes.remove(node)
coord = nodes.new('ShaderNodeTexCoord')
tex = nodes.new('{texture_nodes[texture_type]}')
tex.location = (200, 0)
output = nodes.new('ShaderNodeOutputMaterial')
output.location = (600, 0)
links.new(coord.outputs['UV'], tex.inputs[0])
bpy.ops.mesh.primitive_plane_add(size=2)
plane = bpy.context.object
plane.data.materials.append(mat)
bpy.ops.object.camera_add(location=(0, 0, 2))
cam = bpy.context.object
cam.rotation_euler = (0, 0, 0)
bpy.context.scene.camera = cam
bpy.context.scene.render.resolution_x = {resolution}
bpy.context.scene.render.resolution_y = {resolution}
bpy.context.scene.render.filepath = r"{output_path}"
bpy.ops.render.render(write_still=True)
'''
        result = self.run_script(script)
        if not result["success"]:
            raise RuntimeError(f"Texture generation failed: {result['stderr']}")
        return output_path

    def create_dice(self, dice_type: str, output_path: Path,
                    size: float = 1.0, texture_resolution: int = 1024,
                    export_uv_layout: bool = True,
                    export_svg: bool = True) -> Dict[str, Path]:
        """Create a UV-mapped die and export it."""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        dice_type = dice_type.lower()
        valid_types = ["d4", "d6", "d8", "d10", "d12", "d20"]
        if dice_type not in valid_types:
            raise ValueError(f"Invalid dice type: {dice_type}. Valid: {valid_types}")

        # Simplified dice creation (cube-based for d6, others as primitives)
        script = f'''
import bpy
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()
bpy.ops.mesh.primitive_cube_add(size={size})
obj = bpy.context.object
obj.name = "{dice_type}"
bpy.ops.object.shade_smooth()
bpy.ops.export_scene.gltf(filepath=r"{output_path}", export_format="GLB")
'''
        result = self.run_script(script)
        if not result["success"]:
            raise RuntimeError(f"Dice creation failed: {result['stderr']}")

        paths = {"model_path": output_path}
        return paths

    def create_dice_set(self, output_dir: Path, size: float = 1.0,
                        texture_resolution: int = 1024) -> Dict[str, Dict[str, Path]]:
        """Create a complete set of RPG dice (D4-D20)."""
        output_dir = Path(output_dir)
        results = {}
        for dice_type in ["d4", "d6", "d8", "d10", "d12", "d20"]:
            model_path = output_dir / "models" / f"{dice_type}.glb"
            results[dice_type] = self.create_dice(
                dice_type=dice_type, output_path=model_path,
                size=size, texture_resolution=texture_resolution,
            )
        return results

    def render_isometric_background(self, output_path: Path,
                                    scene_type: str = "landscape",
                                    resolution: tuple = (1920, 1080)) -> Path:
        """Render an isometric background for 2.5D games."""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        script = f'''
import bpy
import math
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()
bpy.ops.mesh.primitive_plane_add(size=20, location=(0, 0, 0))
bpy.ops.object.camera_add()
cam = bpy.context.object
cam.location = (10, -10, 10)
cam.rotation_euler = (math.radians(60), 0, math.radians(45))
cam.data.type = 'ORTHO'
cam.data.ortho_scale = 15
bpy.context.scene.camera = cam
bpy.ops.object.light_add(type='SUN', location=(5, -5, 10))
bpy.context.object.data.energy = 3
bpy.context.scene.render.resolution_x = {resolution[0]}
bpy.context.scene.render.resolution_y = {resolution[1]}
bpy.context.scene.render.image_settings.file_format = 'PNG'
bpy.context.scene.render.filepath = r"{output_path}"
bpy.context.scene.render.film_transparent = True
bpy.ops.render.render(write_still=True)
'''
        result = self.run_script(script)
        if not result["success"]:
            raise RuntimeError(f"Isometric render failed: {result['stderr']}")
        return output_path

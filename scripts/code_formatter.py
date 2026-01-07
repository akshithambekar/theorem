from typing import Dict, List
from agents.code_gen import ManimFile, ManimScene


def format_manim_scene(scene: ManimScene, imports: List[str]) -> str:
    """
    Convert a single ManimScene to a complete Python file string.

    Args:
        scene: ManimScene object with class_name, objects, animations
        imports: List of import statements to include

    Returns:
        Complete Python code as string, ready to write to file
    """
    lines = []

    # 1. Import statements
    if imports:
        lines.extend(imports)
    else:
        lines.append("from manim import *")
    lines.append("")  # Blank line after imports
    lines.append("")  # Double blank line for PEP 8

    # 2. Class definition
    lines.append(f"class {scene.class_name}(Scene):")

    # 3. construct method
    lines.append("    def construct(self):")

    has_content = False

    # 4. Setup code (optional)
    if scene.setup_code:
        lines.append("        # Setup")
        for setup_line in scene.setup_code:
            lines.append(f"        {setup_line}")
        lines.append("")  # Blank line after setup
        has_content = True

    # 5. Object instantiations
    if scene.objects:
        lines.append("        # Objects")
        for obj in scene.objects:
            lines.append(f"        {obj.var_name} = {obj.constructor}")
            if obj.add_to_scene:
                lines.append(f"        self.add({obj.var_name})")
        lines.append("")  # Blank line after objects
        has_content = True

    # 6. Animations
    if scene.animations:
        lines.append("        # Animations")
        for animation in scene.animations:
            if animation.run_time is not None:
                lines.append(f"        self.play({animation.call}, run_time={animation.run_time})")
            else:
                lines.append(f"        self.play({animation.call})")
        has_content = True

    # If no content was added, add pass statement
    if not has_content:
        lines.append("        pass")

    return "\n".join(lines)


def format_manim_file(manim_file: ManimFile) -> Dict[str, str]:
    """
    Convert entire ManimFile to a mapping of filename → Python code.

    Args:
        manim_file: Complete ManimFile object

    Returns:
        Dictionary mapping scene filenames to Python code strings
        Example: {"scene_1.py": "from manim import *\n\nclass ...", ...}
    """
    result = {}

    for scene in manim_file.scenes:
        filename = f"{scene.scene_id}.py"
        code = format_manim_scene(scene, manim_file.imports)
        result[filename] = code

    return result

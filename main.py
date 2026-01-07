from dotenv import load_dotenv
from pathlib import Path
from typing import Dict
from agents.script_gen import generate_script
from agents.scene_gen import generate_scene
from agents.code_gen import generate_code_with_validation, ValidationFailedError
from scripts.code_formatter import format_manim_file

load_dotenv()


def write_scenes_to_files(code_files: Dict[str, str], output_dir: str = "manim_scenes"):
    """
    Write generated Manim scenes to individual Python files.
    
    Args:
        code_files: Dictionary mapping filename to Python code
        output_dir: Directory to write files to
    """
    # Create output directory if it doesn't exist
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    written_files = []
    
    # Write each scene to a separate file
    for filename, code in code_files.items():
        file_path = output_path / filename
        try:
            with open(file_path, 'w') as f:
                f.write(code)
            written_files.append(file_path)
            print(f"✓ Written: {file_path}")
        except Exception as e:
            print(f"✗ Failed to write {file_path}: {e}")
    
    print(f"\n✓ Generated {len(written_files)} scene files in {output_path}/")
    return written_files


def main():
    query = input("What can I help you learn? ")
    try:
        # Generate structured outputs
        print("\n[1/4] Generating script...")
        script = generate_script(query)

        print("[2/4] Generating scene descriptions...")
        scene = generate_scene(script)

        print("[3/4] Generating Manim code with validation...")
        manim_file = generate_code_with_validation(scene, max_retries=3)

        # Convert to Python code and write to files
        print("[4/4] Writing scene files...")
        code_files = format_manim_file(manim_file)
        write_scenes_to_files(code_files)

    except ValidationFailedError as e:
        print(f"\n✗ Code generation failed after {3} attempts")
        print("Failed scenes:")
        for result in e.validation_results:
            if not result.success:
                print(f"  - {result.class_name}: {result.stderr[:200]}...")

    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()

import tempfile
import subprocess
import re
from pathlib import Path
from typing import Dict, List
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, as_completed


@dataclass
class ValidationResult:
    """Result from validating a Manim scene compilation"""
    scene_id: str
    class_name: str
    success: bool
    stderr: str
    code: str
    filename: str


def extract_class_name(code: str) -> str:
    """
    Extract Scene class name from Python code.
    Looks for pattern: class ClassName(Scene):
    """
    match = re.search(r'class\s+(\w+)\(Scene\):', code)
    if not match:
        raise ValueError("No Scene class found in code")
    return match.group(1)


def extract_scene_id(code: str) -> str:
    """
    Extract scene_id from code comments or class name.
    Falls back to class name if no scene_id comment found.
    """
    # Look for # scene_id: xyz comment
    match = re.search(r'#\s*scene_id:\s*(\w+)', code)
    if match:
        return match.group(1)
    # Fallback to class name
    return extract_class_name(code)


def validate_manim_scene(code: str, class_name: str, filename: str) -> ValidationResult:
    """
    Validate single Manim scene by running manim --dry_run.

    Args:
        code: Python code containing Manim scene
        class_name: Name of Scene class to validate
        filename: Original filename (for error reporting)

    Returns:
        ValidationResult with success status and error details
    """
    scene_id = extract_scene_id(code)

    # Write code to temp file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(code)
        temp_path = f.name

    try:
        # Run manim --dry_run
        result = subprocess.run(
            ['manim', '--dry_run', temp_path, class_name],
            capture_output=True,
            text=True,
            timeout=10
        )

        # Success if return code is 0
        success = result.returncode == 0
        stderr = result.stderr

        return ValidationResult(
            scene_id=scene_id,
            class_name=class_name,
            success=success,
            stderr=stderr,
            code=code,
            filename=filename
        )

    except subprocess.TimeoutExpired:
        return ValidationResult(
            scene_id=scene_id,
            class_name=class_name,
            success=False,
            stderr="Error: Manim validation timed out after 10 seconds",
            code=code,
            filename=filename
        )

    finally:
        # Clean up temp file
        Path(temp_path).unlink(missing_ok=True)


def validate_all_scenes(code_files: Dict[str, str], max_workers: int = 4) -> List[ValidationResult]:
    """
    Validate multiple Manim scenes in parallel.

    Args:
        code_files: Dict mapping filename to Python code
        max_workers: Max parallel validations (default 4)

    Returns:
        List of ValidationResult for each scene
    """
    results = []

    # Extract (filename, code, class_name) tuples
    validation_tasks = []
    for filename, code in code_files.items():
        try:
            class_name = extract_class_name(code)
            validation_tasks.append((filename, code, class_name))
        except ValueError as e:
            # No Scene class found - create error result
            results.append(ValidationResult(
                scene_id=filename,
                class_name="Unknown",
                success=False,
                stderr=f"Error: {e}",
                code=code,
                filename=filename
            ))

    # Run validations in parallel
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(validate_manim_scene, code, class_name, filename): filename
            for filename, code, class_name in validation_tasks
        }

        for future in as_completed(futures):
            try:
                result = future.result()
                results.append(result)
            except Exception as e:
                filename = futures[future]
                # Find original code for this filename
                code = code_files[filename]
                results.append(ValidationResult(
                    scene_id=filename,
                    class_name="Unknown",
                    success=False,
                    stderr=f"Validation error: {str(e)}",
                    code=code,
                    filename=filename
                ))

    return results

import re
from dataclasses import dataclass
from typing import List


@dataclass
class ManimError:
    """Parsed Manim compilation error with actionable suggestion"""
    error_type: str
    line_number: int
    message: str
    suggestion: str
    class_name: str = ""  # Extracted class/function name if applicable


def _regex_parse_errors(stderr: str) -> List[ManimError]:
    """
    Parse Python errors from Manim stderr using regex patterns.

    Extracts:
    - Error type (NameError, ImportError, AttributeError, etc.)
    - Line number where error occurred
    - Error message
    - Generates actionable suggestion based on error type
    """
    errors = []

    # Pattern for Python traceback errors
    # Example: NameError: name 'StackRepresentation' is not defined
    error_pattern = r'(\w+Error): (.+)'
    # Pattern for line numbers in traceback
    # Example: File "file.py", line 7, in construct
    line_pattern = r'File "(.+)", line (\d+)'

    # Find all error lines
    error_matches = re.finditer(error_pattern, stderr)

    for error_match in error_matches:
        error_type = error_match.group(1)
        message = error_match.group(2)

        # Find line number by looking backwards in stderr
        # Get text before this error
        text_before = stderr[:error_match.start()]
        line_matches = list(re.finditer(line_pattern, text_before))

        # Use last line number found before this error
        line_number = int(line_matches[-1].group(2)) if line_matches else 0

        # Extract class/function name if present
        class_name = _extract_name_from_error(message, error_type)

        # Generate suggestion based on error type
        suggestion = _generate_suggestion(error_type, message, class_name)

        errors.append(ManimError(
            error_type=error_type,
            line_number=line_number,
            message=message,
            suggestion=suggestion,
            class_name=class_name
        ))

    return errors


def _extract_name_from_error(message: str, error_type: str) -> str:
    """Extract class/function/variable name from error message"""
    if error_type == "NameError":
        # Pattern: name 'ClassName' is not defined
        match = re.search(r"name '(\w+)'", message)
        return match.group(1) if match else ""

    elif error_type == "AttributeError":
        # Pattern: 'Scene' object has no attribute 'method_name'
        match = re.search(r"no attribute '(\w+)'", message)
        return match.group(1) if match else ""

    elif error_type == "ImportError":
        # Pattern: cannot import name 'ClassName'
        match = re.search(r"import name '(\w+)'", message)
        return match.group(1) if match else ""

    return ""


def _generate_suggestion(error_type: str, message: str, class_name: str) -> str:
    """Generate actionable suggestion based on error type"""

    if error_type == "NameError":
        return (
            f"Class/function '{class_name}' does not exist in Manim. "
            f"Use manim_doc_reference to validate class exists."
        )

    elif error_type == "ImportError":
        if class_name:
            return (
                f"'{class_name}' cannot be imported. "
                f"Verify it exists in Manim or check version compatibility."
            )
        return "Invalid import. Check Manim version compatibility."

    elif error_type == "AttributeError":
        return (
            f"Method/property '{class_name}' does not exist. "
            f"Use manim_doc_reference to verify correct API."
        )

    elif error_type == "TypeError":
        return "Incorrect arguments or types. Check Manim documentation for correct usage."

    elif error_type == "SyntaxError":
        return "Python syntax error. Check for missing parentheses, colons, or indentation."

    else:
        return "Check Manim documentation and verify code syntax."


def _llm_parse_errors(stderr: str) -> List[ManimError]:
    """
    Future: LLM-based intelligent error parsing.
    Uses language model to understand context and provide smarter suggestions.
    """
    raise NotImplementedError(
        "LLM-based error parsing not yet implemented. "
        "Use use_llm=False for regex-based parsing."
    )


def parse_manim_errors(stderr: str, use_llm: bool = False) -> List[ManimError]:
    """
    Parse Manim compilation errors from stderr.

    Args:
        stderr: Error output from manim --dry_run
        use_llm: Use LLM for intelligent parsing (future feature)

    Returns:
        List of parsed errors with suggestions

    Note:
        Pluggable architecture allows future LLM upgrade while maintaining
        same interface. Currently uses regex-based parsing (use_llm=False).
    """
    if use_llm:
        return _llm_parse_errors(stderr)
    else:
        return _regex_parse_errors(stderr)

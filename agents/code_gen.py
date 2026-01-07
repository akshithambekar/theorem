from dotenv import load_dotenv
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI  # pyright: ignore[reportMissingImports]
from langchain_anthropic import ChatAnthropic # pyright: ignore[reportMissingImports]
from langchain_core.prompts import ChatPromptTemplate # pyright: ignore[reportMissingImports]
from langchain_core.output_parsers import PydanticOutputParser # pyright: ignore[reportMissingImports]
from langchain.agents import create_tool_calling_agent, AgentExecutor # pyright: ignore[reportMissingImports]
from typing import List, Optional, Dict
from agents.scene_gen import SceneDescription
from tools import manim_tool
from scripts.manim_validator import validate_all_scenes, ValidationResult
from scripts.error_parser import parse_manim_errors, ManimError

load_dotenv()

class ManimObject(BaseModel):
    object_id: str = Field(description="matches ScenePlan.object_id")
    var_name: str = Field(description="Python variable name")
    constructor: str = Field(description="Manim constructor call")
    add_to_scene: bool = Field(description="whether to immediately add to scene")

class ManimAnimation(BaseModel):
    animation_id: str = Field(description="matches Action.action_id")
    call: str = Field(description="self.play(...) call")
    run_time: Optional[float] = Field(default=None, description="explicit run_time if specified")

class ManimScene(BaseModel):
    scene_id: str = Field(description="matches ScenePlan.scene_id")
    class_name: str = Field(description="Python class name for Manim scene")
    setup_code: Optional[List[str]] = Field(default=None, description="initialization code before animations")
    objects: List["ManimObject"]
    animations: List["ManimAnimation"]

class ManimFile(BaseModel):
    imports: List[str] = Field(description="Manim and Python imports required")
    scenes: List["ManimScene"]

def generate_code(scene: SceneDescription, error_feedback: Optional[str] = None):
    """
    Generate Manim code from scene description.

    Args:
        scene: SceneDescription from scene_gen agent
        error_feedback: Optional error feedback from previous validation failure

    Returns:
        ManimFile or Exception on parsing failure
    """
    scene_json = scene.model_dump_json()
    llm = ChatAnthropic(temperature=0.1, model="claude-3-7-sonnet-20250219")
    parser = PydanticOutputParser(pydantic_object=ManimFile)
    with open("prompts/code_gen.md", "r") as f:
        system_prompt = f.read()

    # Build prompt with error feedback if provided
    messages = [
        ("system", system_prompt),
        ("placeholder", "{chat_history}"),
        ("human", "{scene_json}")
    ]

    # Add error feedback message if retrying
    if error_feedback:
        messages.append(("human", "{error_feedback}"))

    messages.append(("placeholder", "{agent_scratchpad}"))

    prompt = ChatPromptTemplate.from_messages(messages).partial(
        format_instructions=parser.get_format_instructions()
    )

    tools = [manim_tool]
    agent = create_tool_calling_agent(
        llm=llm,
        prompt=prompt,
        tools=tools
    )
    context_agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

    # Invoke with or without error feedback
    invoke_input = {"scene_json": scene_json}
    if error_feedback:
        invoke_input["error_feedback"] = error_feedback

    raw_response = context_agent_executor.invoke(invoke_input)
    try:
        structured_response = parser.parse(raw_response.get("output"))
        return structured_response
    except Exception as e:
        print(f"Error parsing response: {e}")
        return e


def _identify_root_causes(errors: List[ManimError]) -> str:
    """Identify root causes from parsed errors"""
    causes = []
    for error in errors:
        if error.class_name:
            causes.append(f"  - {error.class_name}: {error.suggestion}")
        else:
            causes.append(f"  - {error.error_type}: {error.message}")
    return "\n".join(causes) if causes else "  - Unknown error"


def _generate_action_items(errors: List[ManimError]) -> str:
    """Generate actionable steps from errors"""
    actions = []

    # Collect unique error types
    name_errors = [e for e in errors if e.error_type == "NameError"]
    attr_errors = [e for e in errors if e.error_type == "AttributeError"]
    import_errors = [e for e in errors if e.error_type == "ImportError"]

    action_num = 1

    if name_errors:
        actions.append(f"  {action_num}. Use manim_doc_reference to search for valid class names")
        actions.append("     - Query keywords based on semantic meaning (e.g., 'group', 'container', 'text')")
        actions.append("     - Validate each result exists before using")
        action_num += 1

    if attr_errors:
        actions.append(f"  {action_num}. Use manim_doc_reference to search for valid methods/animations")
        actions.append("     - Query keywords based on desired effect (e.g., 'highlight', 'transform', 'fade')")
        actions.append("     - Validate each result exists before using")
        action_num += 1

    if import_errors:
        actions.append(f"  {action_num}. Fix import statements")
        actions.append("     - Only import from 'manim' package")
        actions.append("     - Remove any non-existent imports")
        action_num += 1

    actions.append(f"  {action_num}. Replace ALL hallucinated classes with confirmed Manim APIs")
    actions.append(f"  {action_num + 1}. Query manim_doc_reference for EVERY class before outputting")

    return "\n".join(actions) if actions else "  1. Review error and correct code"


def format_feedback_for_agent(
    validation_results: List[ValidationResult],
    attempt_num: int,
    max_retries: int
) -> str:
    """
    Format validation errors as rich feedback for code_gen agent.

    Args:
        validation_results: List of validation results (may include failures)
        attempt_num: Current attempt number (1-indexed)
        max_retries: Maximum retries allowed

    Returns:
        Formatted feedback string for agent
    """
    feedback = f"⚠️ VALIDATION FAILED - Attempt {attempt_num}/{max_retries}\n\n"

    for result in validation_results:
        if not result.success:
            feedback += f"SCENE: {result.class_name} (scene_id: {result.scene_id})\n"
            feedback += f"STATUS: Compilation error\n\n"
            feedback += "━━━ MANIM ERROR OUTPUT ━━━\n"
            feedback += result.stderr + "\n"
            feedback += "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            feedback += "FAILED CODE YOU GENERATED:\n```python\n"
            feedback += result.code + "\n```\n\n"

            # Parse errors
            parsed_errors = parse_manim_errors(result.stderr)

            if parsed_errors:
                feedback += "ERROR ANALYSIS:\n"
                for error in parsed_errors:
                    feedback += f"  Line {error.line_number}: {error.error_type} - {error.message}\n"

                feedback += "\nROOT CAUSE:\n"
                feedback += _identify_root_causes(parsed_errors) + "\n"

                feedback += "\nREQUIRED ACTIONS:\n"
                feedback += _generate_action_items(parsed_errors) + "\n\n"

    feedback += "\nCRITICAL: Only use classes that manim_doc_reference confirms exist.\n"
    feedback += "Do NOT assume any class exists without tool validation.\n"
    feedback += "Regenerate the ManimFile with validated Manim APIs only."

    return feedback


class ValidationFailedError(Exception):
    """Raised when validation fails after max retries"""
    def __init__(self, message: str, validation_results: List[ValidationResult]):
        self.validation_results = validation_results
        super().__init__(message)


def generate_code_with_validation(
    scene: SceneDescription,
    max_retries: int = 3
) -> ManimFile:
    """
    Generate Manim code with validation feedback loop.

    Args:
        scene: SceneDescription from scene_gen agent
        max_retries: Maximum retry attempts (default 3)

    Returns:
        Validated ManimFile

    Raises:
        ValidationFailedError: If validation fails after max_retries

    Process:
        1. Generate code with code_gen agent
        2. Format and validate with manim --dry_run
        3. If errors: parse, format feedback, retry
        4. If success: return ManimFile
    """
    # Lazy import to avoid circular dependency
    from scripts.code_formatter import format_manim_file

    feedback = None

    for attempt in range(1, max_retries + 1):
        print(f"\n[Code Gen] Attempt {attempt}/{max_retries}...")

        # Generate code (with feedback if retrying)
        manim_file = generate_code(scene, error_feedback=feedback)

        # Check if parsing failed
        if isinstance(manim_file, Exception):
            print(f"[Code Gen] Parsing failed: {manim_file}")
            if attempt == max_retries:
                raise ValidationFailedError(
                    f"Code generation parsing failed after {max_retries} attempts",
                    []
                )
            feedback = f"Previous attempt failed to generate valid JSON. Error: {manim_file}\nEnsure output matches ManimFile schema exactly."
            continue

        # Format to Python code
        code_files = format_manim_file(manim_file)

        # Validate all scenes
        print(f"[Code Gen] Validating {len(code_files)} scenes...")
        validation_results = validate_all_scenes(code_files)

        # Check for failures
        failed = [r for r in validation_results if not r.success]

        if not failed:
            print(f"[Code Gen] ✓ All scenes validated successfully")
            return manim_file

        # Format feedback for retry
        print(f"[Code Gen] ✗ {len(failed)}/{len(validation_results)} scenes failed validation")
        feedback = format_feedback_for_agent(failed, attempt, max_retries)

    # Max retries exceeded
    raise ValidationFailedError(
        f"Validation failed after {max_retries} attempts",
        validation_results
    )

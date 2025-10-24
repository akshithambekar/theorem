from dotenv import load_dotenv
from typing import TypedDict, Annotated
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI  # pyright: ignore[reportMissingImports]
from langchain_core.prompts import ChatPromptTemplate  # pyright: ignore[reportMissingImports]
from langchain_core.output_parsers import PydanticOutputParser  # pyright: ignore[reportMissingImports]
from langgraph.graph import StateGraph, END  # pyright: ignore[reportMissingImports]

load_dotenv()


class LessonSection(BaseModel):
    """A section of the 2-minute video lesson"""
    name: str = Field(description="Name of the section (Hook, Core Concept, Example, or Takeaway)")
    time_seconds: str = Field(description="Time allocation in seconds (e.g., '15-20 seconds')")
    key_points: list[str] = Field(description="Key points to cover in this section")
    teaching_approach: str = Field(description="Suggested visual or teaching approach")


class TwoMinuteLessonPlan(BaseModel):
    """A complete lesson plan for a 2-minute video"""
    topic: str = Field(description="The topic being taught")
    target_audience: str = Field(description="Who this video is for")
    hook: LessonSection = Field(description="Hook section (0-15 seconds)")
    core_concept: LessonSection = Field(description="Core concept section (45-60 seconds)")
    example: LessonSection = Field(description="Example/demonstration section (30-45 seconds)")
    takeaway: LessonSection = Field(description="Takeaway section (15-20 seconds)")
    total_time: str = Field(description="Total estimated time", default="120 seconds")


class PlanningState(TypedDict):
    """State for the planning agent graph"""
    topic: str
    lesson_plan: TwoMinuteLessonPlan | None
    error: str | None


def create_lesson_plan(state: PlanningState) -> PlanningState:
    """
    Node that creates a lesson plan for the given topic
    """
    topic = state["topic"]

    try:
        llm = ChatOpenAI(model="gpt-4o-mini")
        parser = PydanticOutputParser(pydantic_object=TwoMinuteLessonPlan)

        with open("prompts/planning_agent_prompt.txt", "r") as f:
            system_prompt = f.read()

        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", "Create a 2-minute video lesson plan for the topic: {topic}")
        ]).partial(format_instructions=parser.get_format_instructions())

        chain = prompt | llm | parser
        lesson_plan = chain.invoke({"topic": topic})

        return {
            "topic": topic,
            "lesson_plan": lesson_plan,
            "error": None
        }
    except Exception as e:
        return {
            "topic": topic,
            "lesson_plan": None,
            "error": str(e)
        }


def should_continue(state: PlanningState) -> str:
    """
    Conditional edge that determines if we should end or retry
    """
    if state["error"]:
        return "error"
    return "success"


def create_planning_agent():
    """
    Creates and returns a LangGraph agent for planning 2-minute video lessons
    """
    # Create the graph
    workflow = StateGraph(PlanningState)

    # Add nodes
    workflow.add_node("create_plan", create_lesson_plan)

    # Set the entry point
    workflow.set_entry_point("create_plan")

    # Add conditional edges
    workflow.add_conditional_edges(
        "create_plan",
        should_continue,
        {
            "success": END,
            "error": END
        }
    )

    # Compile the graph
    app = workflow.compile()

    return app


def run_planning_agent(topic: str) -> TwoMinuteLessonPlan | None:
    """
    Main function to run the planning agent

    Args:
        topic: The topic the user wants to learn

    Returns:
        A TwoMinuteLessonPlan object or None if there was an error
    """
    agent = create_planning_agent()

    # Run the agent
    result = agent.invoke({
        "topic": topic,
        "lesson_plan": None,
        "error": None
    })

    if result["error"]:
        print(f"Error creating lesson plan: {result['error']}")
        return None

    return result["lesson_plan"]


def print_lesson_plan(lesson_plan: TwoMinuteLessonPlan) -> None:
    """
    Pretty print a lesson plan
    """
    print("\n" + "="*60)
    print(f"2-MINUTE VIDEO LESSON PLAN: {lesson_plan.topic}")
    print("="*60)
    print(f"\nTarget Audience: {lesson_plan.target_audience}")
    print(f"Total Time: {lesson_plan.total_time}\n")

    sections = [
        ("HOOK", lesson_plan.hook),
        ("CORE CONCEPT", lesson_plan.core_concept),
        ("EXAMPLE/DEMONSTRATION", lesson_plan.example),
        ("TAKEAWAY", lesson_plan.takeaway)
    ]

    for section_name, section in sections:
        print(f"\n{section_name} ({section.time_seconds})")
        print("-" * 60)
        print(f"Teaching Approach: {section.teaching_approach}")
        print("\nKey Points:")
        for i, point in enumerate(section.key_points, 1):
            print(f"  {i}. {point}")

    print("\n" + "="*60 + "\n")


if __name__ == "__main__":
    # Example usage
    topic = input("What topic would you like to create a 2-minute lesson for? ")

    print(f"\nCreating lesson plan for: {topic}...")
    lesson_plan = run_planning_agent(topic)

    if lesson_plan:
        print_lesson_plan(lesson_plan)
    else:
        print("Failed to create lesson plan. Please try again.")

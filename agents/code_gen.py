from dotenv import load_dotenv
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI  # pyright: ignore[reportMissingImports]
# from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import ChatPromptTemplate # pyright: ignore[reportMissingImports]
from langchain_core.output_parsers import PydanticOutputParser # pyright: ignore[reportMissingImports]
from langchain.agents import create_tool_calling_agent, AgentExecutor # pyright: ignore[reportMissingImports]
from typing import List, Optional
from agents.scene_gen import SceneDescription
from tools import manim_tool

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

def generate_code(scene: SceneDescription):
    scene_json = scene.model_dump_json()
    llm = ChatOpenAI(temperature=0.2, model="gpt-4o-mini") # TODO: change to claude-3.7-sonnet or claude-4.0-sonnet
    parser = PydanticOutputParser(pydantic_object=ManimFile)
    with open("prompts/code_gen.md", "r") as f:
        system_prompt = f.read()
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            ("placeholder", "{chat_history}"),
            ("human", "{scene_json}"),
            ("placeholder", "{agent_scratchpad}")
        ]
    ).partial(format_instructions=parser.get_format_instructions())
    tools = [manim_tool]
    agent = create_tool_calling_agent(
        llm=llm,
        prompt=prompt,
        tools=tools
    )
    context_agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)
    raw_response = context_agent_executor.invoke({"scene_json": scene_json})
    try:
        structured_response = parser.parse(raw_response.get("output"))
        return structured_response
    except Exception as e:
        print(f"Error parsing response: {e}")
        return e

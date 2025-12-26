from dotenv import load_dotenv
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI  # pyright: ignore[reportMissingImports]
from langchain_core.prompts import ChatPromptTemplate # pyright: ignore[reportMissingImports]
from langchain_core.output_parsers import PydanticOutputParser # pyright: ignore[reportMissingImports]
from langchain.agents import create_tool_calling_agent, AgentExecutor # pyright: ignore[reportMissingImports]
from typing import List, Optional

load_dotenv()

class Constraint(BaseModel):
    name: str = Field(description="semantic constraint, such as 'right_angle', 'orthogonal', 'colinear'")
    value: any = Field(description="constraint value/parameter, such as true, 90, 'origin'")

class Object(BaseModel):
    object_id: str = Field(description="identifier for referencing across beats")
    type: str = Field("conceptual type, such as triangle, vector, point, curve")
    constraints: Optional[List[Constraint]] = Field(default=None, description="geometric or relational constraints")
    labels: Optional[List[str]] = Field(default=None, description="optional labels visible on screen")

class Action(BaseModel):
    action_id: str = Field(description="identifier for this action")
    action_type: str = Field(description="action type, such as create, transform, highlight, remove, etc.")
    targets: List[str] = Field(description="object_id(s) this action applies to")
    description: str = Field(description="high-level description of what happens visually")
    sync_cue_id: Optional[str] = Field(default=None, description="optional reference to a sync cue from the beat")
    duration: Optional[float] = Field(default=None, description="approximate time this action occupies within the beat") 

class ScenePlan(BaseModel):
    scene_id: str = Field(description="identifier for this scene")
    beat_id: str = Field(description="beat identifier, must match the originating beat")
    continuity: bool = Field(description="true if visual state continues from previous scene")
    objects: List[Object] = Field(description="objects that exist or are introduced in this scene")
    actions: List[Action] = Field(description="ordered list of visual actions")
    end_state_summary: str = Field(description="human-readable summary of final visual state")

class SceneDescription(BaseModel):
    scenes: List[ScenePlan]

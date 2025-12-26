from dotenv import load_dotenv
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI  # pyright: ignore[reportMissingImports]
from langchain_core.prompts import ChatPromptTemplate # pyright: ignore[reportMissingImports]
from langchain_core.output_parsers import PydanticOutputParser # pyright: ignore[reportMissingImports]
from langchain.agents import create_tool_calling_agent, AgentExecutor # pyright: ignore[reportMissingImports]
from typing import List, Optional

load_dotenv()

class SyncCue(BaseModel):
    cue_text_fragment: str = Field(description="exact substring from narration_text for sync anchoring")
    cue_intent: str = Field(description="high-level intent such as 'pause', 'transition', 'emphasize', etc.")

class Beat(BaseModel):
    beat_id: str = Field(description="identifier for usage across visuals. audio, and stitching")
    narration_text: str = Field(description="spoken narration for this beat")
    duration: float = Field(description="duration for visuals and narration")
    concept_goal: str = Field(description="idea that the user must understand after this beat")
    continuity: bool = Field(description="whether this beat starts from a fresh visual state or continues from the prior state. True = continues previous state, False = fresh visual state")
    sync_cues: Optional[List[SyncCue]] = None

class TimingModel(BaseModel):
    basis: str = Field(description="how timing was estimated")
    flexibility: str = Field(description="allowed deviation from estimated timing")

class ScriptGeneration(BaseModel):
    metadata: dict = Field(description="inferred assumptions like audience, scope, exclusions")
    beats: List[Beat]
    timing_model: TimingModel

def generate_script(query: str):
    llm = ChatOpenAI(model="gpt-4o-mini")
    parser = PydanticOutputParser(pydantic_object=ScriptGeneration)
    with open("prompts/script_gen.md", "r") as f:
        system_prompt = f.read()
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            ("placeholder", "{chat_history}"),
            ("human", "{query}"),
            ("placeholder", "{agent_scratchpad}")
        ]
    ).partial(format_instructions=parser.get_format_instructions())
    tools = []
    agent = create_tool_calling_agent(
        llm=llm,
        prompt=prompt,
        tools=tools
    )
    context_agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)
    raw_response = context_agent_executor.invoke({"query": query})
    
    try:
        structured_response = parser.parse(raw_response.get("output"))
        return structured_response
    except Exception as e:
        print(f"Error parsing response: {e}")
        return e

def main():
    user_prompt = input("What can I help you learn? ")
    generate_script(user_prompt)

if __name__ == "__main__":
    main()

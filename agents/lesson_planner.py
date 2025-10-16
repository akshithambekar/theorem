from dotenv import load_dotenv
from pydantic import BaseModel
from langchain_openai import ChatOpenAI  # pyright: ignore[reportMissingImports]
from langchain_core.prompts import ChatPromptTemplate # pyright: ignore[reportMissingImports]
from langchain_core.output_parsers import PydanticOutputParser # pyright: ignore[reportMissingImports]
from langchain.agents import create_tool_calling_agent, AgentExecutor # pyright: ignore[reportMissingImports]
load_dotenv()

class LessonPlan(BaseModel):
    topic: str
    learning_objectives: list[str]
    prerequisites: list[str]
    misconceptions: list[str]
    angles: list[str]
    tools_used: list[str]

def lesson_planner_agent(context_data):
    llm = ChatOpenAI(model="gpt-4o-mini")
    parser = PydanticOutputParser(pydantic_object=LessonPlan)
    with open("prompts/lesson_planner_prompt.txt", "r") as f:
        system_prompt = f.read()

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            ("placeholder", "{chat_history}"),
            ("human", "{context_data}"),
            ("placeholder", "{agent_scratchpad}")
        ]
    ).partial(format_instructions=parser.get_format_instructions())

    tools = []
    agent = create_tool_calling_agent(
        llm=llm,
        prompt=prompt,
        tools=tools
    )

    lesson_agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)
    raw_response = lesson_agent_executor.invoke({"context_data": str(context_data)})

    try:
        structured_response = parser.parse(raw_response.get("output"))
        return structured_response
    except Exception as e:
        print(f"Error parsing response: {e}")
        return e
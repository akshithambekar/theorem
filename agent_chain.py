from dotenv import load_dotenv
from pydantic import BaseModel
from langchain_openai import ChatOpenAI  # pyright: ignore[reportMissingImports]
from langchain_core.prompts import ChatPromptTemplate # pyright: ignore[reportMissingImports]
from langchain_core.output_parsers import PydanticOutputParser # pyright: ignore[reportMissingImports]
from langchain.chains import LLMChain, SequentialChain # pyright: ignore[reportMissingImports]
from langchain_core.output_parsers import StrOutputParser # pyright: ignore[reportMissingImports]

load_dotenv()

class ContextResponse(BaseModel):
    topic: str
    learning_objectives: list[str]
    prerequisites: list[str]
    misconceptions: list[str]
    angles: list[str]
    tools_used: list[str]

class LessonPlan(BaseModel):
    topic: str
    learning_objectives: list[str]
    prerequisites: list[str]
    misconceptions: list[str]
    angles: list[str]
    tools_used: list[str]

def create_agent_chain():
    llm = ChatOpenAI(model="gpt-4o-mini")

    # Context Analysis Chain
    context_parser = PydanticOutputParser(pydantic_object=ContextResponse)
    with open("prompts/analyze_context_prompt.txt", "r") as f:
        context_system_prompt = f.read()

    context_prompt = ChatPromptTemplate.from_messages([
        ("system", context_system_prompt),
        ("human", "{query}")
    ]).partial(format_instructions=context_parser.get_format_instructions())

    context_chain = LLMChain(
        llm=llm,
        prompt=context_prompt,
        output_key="context_analysis",
        verbose=True
    )

    # Lesson Planning Chain
    lesson_parser = PydanticOutputParser(pydantic_object=LessonPlan)
    with open("prompts/lesson_planner_prompt.txt", "r") as f:
        lesson_system_prompt = f.read()

    lesson_prompt = ChatPromptTemplate.from_messages([
        ("system", lesson_system_prompt),
        ("human", "Based on this context analysis: {context_analysis}")
    ]).partial(format_instructions=lesson_parser.get_format_instructions())

    lesson_chain = LLMChain(
        llm=llm,
        prompt=lesson_prompt,
        output_key="lesson_plan",
        verbose=True
    )

    # Sequential Chain that connects both
    agent_chain = SequentialChain(
        chains=[context_chain, lesson_chain],
        input_variables=["query"],
        output_variables=["context_analysis", "lesson_plan"],
        verbose=True
    )

    return agent_chain, context_parser, lesson_parser

def run_chained_agents(query: str):
    chain, context_parser, lesson_parser = create_agent_chain()
    # Run the chain
    result = chain({"query": query})

    try:
        context_data = context_parser.parse(result["context_analysis"])
        lesson_data = lesson_parser.parse(result["lesson_plan"])
        return {
            "context": context_data,
            "lesson_plan": lesson_data
        }
    except Exception as e:
        print(f"Error parsing responses: {e}")
        return {
            "context": result["context_analysis"],
            "lesson_plan": result["lesson_plan"]
        }
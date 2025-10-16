from dotenv import load_dotenv
from pydantic import BaseModel
from langchain_openai import ChatOpenAI  # pyright: ignore[reportMissingImports]
from langchain_core.prompts import ChatPromptTemplate # pyright: ignore[reportMissingImports]
from langchain_core.output_parsers import PydanticOutputParser # pyright: ignore[reportMissingImports]
from langchain.agents import create_tool_calling_agent, AgentExecutor # pyright: ignore[reportMissingImports]
from tools import search_tool, wikipedia_tool, save_to_txt_tool
from agents.analyze_context import analyze_context
from agents.lesson_planner import lesson_planner_agent
from agent_chain import run_chained_agents

load_dotenv()

def main():
    query = input("What can I help you learn? ")
    run_chained_agents(query)

if __name__ == "__main__":
    main()

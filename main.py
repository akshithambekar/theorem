from dotenv import load_dotenv
from pydantic import BaseModel
from langchain_openai import ChatOpenAI  # pyright: ignore[reportMissingImports]
from langchain_core.prompts import ChatPromptTemplate # pyright: ignore[reportMissingImports]
from langchain_core.output_parsers import PydanticOutputParser, StrOutputParser # pyright: ignore[reportMissingImports]
from langchain.chains import LLMChain, SequentialChain # pyright: ignore[reportMissingImports]
from langchain.agents import create_tool_calling_agent, AgentExecutor # pyright: ignore[reportMissingImports]

from agents.script_gen import generate_script
from agents.scene_gen import generate_scene

load_dotenv()

def main():
    query = input("What can I help you learn? ")
    try:
        script = generate_script(query)
        scene = generate_scene(script)
    except Exception as e:
        print(e)

if __name__ == "__main__":
    main() 

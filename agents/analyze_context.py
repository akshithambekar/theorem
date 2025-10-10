from dotenv import load_dotenv
import os
from openai import OpenAI

load_dotenv()
client = OpenAI()

with open('prompts/analyze_context_prompt.txt', 'r') as file:
    analyze_context_prompt = file.read()

def analyze_context(input_text):
    response = client.responses.create(model="gpt-5-mini", input=analyze_context_prompt.format(input_text=input_text))
    return response.output_text

print('Analyzing context')
response = analyze_context("Explain the Pythagorean Theorem")
print(response.output_text)
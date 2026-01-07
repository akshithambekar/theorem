from langchain.tools import Tool # pyright: ignore[reportMissingImports]
import requests
import os
import json

def manim_doc_reference(query: str) -> str:
    context7_api_key = os.getenv("CONTEXT7_API_KEY")
    if not context7_api_key:
        return "Error: context7 API key not set"
    if not query or not query.strip():
        return "Error: query cannot be empty"

    url = "https://context7.com/api/v2/context"
    headers = {
        "CONTEXT7_API_KEY": f"{context7_api_key}"
    }
    params = {
        "libraryId": "/3b1b/manim",
        "query": query,
        "type": "json"
    }

    try:
        response = requests.get(url, headers=headers, params=params, timeout=10)
        response.raise_for_status()
    except requests.exceptions.Timeout:
        return "Error: context7 API request timed out after 10 seconds"
    except requests.exceptions.ConnectionError:
        return "Error: Could not connect to context7 API. Check your internet connection."
    except requests.exceptions.HTTPError:
        return f"Error: context7 API returned status {response.status_code}"
    except requests.exceptions.RequestException as e:
        return f"Error: Request failed: {str(e)}"

    try:
        result = response.json()
    except json.JSONDecodeError as e:
        return f"Error: Invalid JSON response: {str(e)}"

    if not result:
        return "Error: Empty response from context7"
    if "codeSnippets" not in result:
        return f"Error: Unexpected response format"
    if not result["codeSnippets"]:
        return "No Manim documentation found for this query"
    return json.dumps(result, indent=2)

manim_tool = Tool(
    name="manim_doc_reference",
    func=manim_doc_reference,
    description="REQUIRED: Validate Manim class/animation exists before using. Query EVERY constructor and animation call to ensure it's a real Manim API. Returns documentation if exists, error if not."
)

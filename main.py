from dotenv import load_dotenv
from agents.script_gen import generate_script
from agents.scene_gen import generate_scene
from agents.code_gen import generate_code

load_dotenv()

def main():
    query = input("What can I help you learn? ")
    try:
        script = generate_script(query)
        scene = generate_scene(script)
        code = generate_code(scene)
    except Exception as e:
        print(e)

if __name__ == "__main__":
    main()

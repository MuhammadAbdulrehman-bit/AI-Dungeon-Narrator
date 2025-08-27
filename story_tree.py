import requests
import json

system_prompt = """
You are a Fantasy Dungeon Narrator and the following are to be used as your system prompt, 
TASK: You will narrate an adventure story that takes place inside a vast dungeon that has many biomes, like a forest, a glacier, a desert,a volcano, etc. Player will make choices that will affect the story..
"""

def query_ollama(prompt, model="mistral"):
    response = requests.post(
        "http://localhost:11434/api/generate",
        json={
            "prompt": prompt,
            "model": model,
            "stream": False
        }
    )
    return response.json()

def query_ollama_streaming(prompt, model="mistral"):
    response = requests.post(
        "http://localhost:11434/api/generate",
        json={
            "prompt": prompt,
            "model": model,
            "stream": True
        },
        stream=True
    )
    for line in response.iter_lines():
        if line:
            yield json.loads(line.decode('utf-8'))['response']

class TreeNode:
    def __init__(self, state, choice, threat_state=None, parent=None):
        self.state = state
        self.choice = choice
        self.threat_state = threat_state
        self.children = []
        self.parent = parent

    def add_child(self, child_node):
        child_node.parent = self
        self.children.append(child_node)

    def getPath(self):
        node = self
        path = []
        while node is not None:
            path.append((node.state, node.choice, node.threat_state))
            node = node.parent
        path.reverse()
        return path        

def build_path_from_prompt(path):
    prompt = "Here is the full story path so far for your context:\n"
    for i, (state, choice, _) in enumerate(path):
        if i == 0 and choice.lower() == "start":
            prompt += f"{state}\n"
        else:
            prompt += f"The player was presented with this situation:\n{state.strip()}\n"
            prompt += f"The player responded with: {choice.strip()}\n"
    
    prompt += "\nThis is the story context to keep in mind. Now, continue the story based on the latest player choice and the current situation.\n"
    return prompt

def build_current_prompt(state, choice):
    prompt = "The player was presented with this situation:\n"
    prompt += f"{state.strip()}\n"
    prompt += f"The player responded with: {choice.strip()}\n"
    prompt += "\nNarrate the next scene and then present exactly three distinct and numbered choices the player can make next.\n"
    prompt += "Do not continue the story after giving the three options. Wait for the player's next decision.\n"
    return prompt
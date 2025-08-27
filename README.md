# 🧙 AI Dungeon Master – Interactive Storytelling with Memory

An **AI-powered text adventure game** where the model acts as a Dungeon Master, narrating scenarios and presenting choices.  
Unlike typical story generators, this system **remembers past events** using a custom memory system to keep the story consistent.

---

## 🚀 Features
- 🎮 Interactive gameplay – user makes choices, AI continues the story.
- 🧠 **Memory persistence** – facts/events are stored and reinjected to maintain story consistency.
- 🌲 **Tree structure** – tracks branching storylines for replayability.
- ⏳ **Priority queue system** – ensures important memory facts are never forgotten.
- 💻 **PyQt6 GUI** – clean interface with real-time streaming of responses.
- 🔗 Works with **local LLMs** (Mistral via Ollama API).

---

## 🏗️ Project Architecture
```plaintext
User Input --> GUI (PyQt6) --> LLM (via Ollama API)
       |                                |
       v                                v
   Displayed <-- Memory Manager (Tree + Priority Queue)
```


## 📸 Screenshots / Demo
> *(Optional – Add images or GIFs here for a visual preview of the game in action)*

---

## ⚙️ Installation & Setup

### 1️⃣ Clone the Repository
```bash
git clone https://github.com/your-username/ai-dungeon-master.git
cd ai-dungeon-master
```

## Install Dependencies


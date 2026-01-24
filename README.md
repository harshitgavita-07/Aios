# Aios – Offline Desktop AI Assistant

Aios is a local, offline AI desktop assistant that runs entirely on your machine using an on-device LLM (via Ollama). Your prompts and responses stay on your device and are never sent to any cloud service.[file:3][file:5]

A floating bubble sits on top of your desktop; click it to open a chat window and talk to the assistant in natural language.[file:3][file:4][file:7]

---

## Features

- Fully local inference using an Ollama model (default configurable in `llm.py`).[file:5]  
- Floating, draggable bubble that stays on top of other windows for quick access.[file:3][file:4]  
- Clean chat UI built with PySide6 (Qt) for questions and responses.[file:3][file:7]  
- Simple agent/router + brain architecture so you can plug in your own logic.[file:2][file:6]  
- Graceful error handling and fallback messages if the model or brain is not available.[file:2][file:7]

---

## Project structure

- `app.py` – Entry point; starts the Qt application, creates the assistant window, and shows the floating bubble.[file:3]  
- `bubble.py` – Implements the always-on-top circular bubble that you can drag and click to open the assistant.[file:4]  
- `ui.py` – Main chat UI (`DesktopAssistant` widget) with message area, text input, and send button.[file:7]  
- `agent.py` – Central router that forwards all user input to the brain.[file:2]  
- `brain.py` – Simple brain layer that cleans input and calls the LLM, with basic safeguards.[file:6]  
- `llm.py` – Thin wrapper around Ollama; runs a local LLM model and returns text responses.[file:5]

---

## Installation

Follow these steps to run the assistant on your PC or laptop.

1. **Clone the repository**
   (bash)
   git clone https://github.com/harshitgavita-07/Aios.git


2.Enter the project folder
(Bash)
cd Aios

3. Create a virtual environment
(bash)

python -m venv venv

4.Activate the virtual environment
Windows (PowerShell):
(bash)
venv\Scripts\Activate

macOS / Linux (bash):
source venv/bin/activate

5.Install dependencies

(bash)
pip install -r requirements.txt.

6. Install Ollama and pull a local model

Install Ollama from: https://ollama.com
Then pull a model (example):
(bash)
ollama pull llama3.1:8b

## Make sure the MODEL constant in llm.py matches the model you pulled.[file:5] ##

7. Run the desktop assistant
(bash)

python app.py


A small floating bubble will appear on your desktop. Click it to open the main chat window and start talking to your local assistant.[file:3][file:4][file:7]

## Usage ##

Click the bubble once to open the Desktop AI Assistant V1 window.[file:3][file:4][file:7]
Type your question in the input field at the bottom and press Enter or click Send.[file:7]
The assistant output will appear in the chat area, and the view will auto-scroll to the newest messages.[file:7]
If the agent or LLM is not available, the UI shows clear system or runtime error messages instead of crashing.[file:2][file:5][file:7]

## About the creator ##
Hi, I am Gavita Harshit , a developer passionate about building practical AI tools that run locally and respect user privacy.
This project is a demonstration of on-device intelligence, showing how modern LLMs can power a desktop assistant without any cloud dependency.

You can connect with me and explore more of my work here:

GitHub: https://github.com/harshitgavita-07

LinkedIn / Portfolio: www.linkedin.com/in/harshit-gavita-bb90b3202

Feel free to fork this repository, open issues, or suggest new features to make this offline assistant even more powerful and user-friendly.


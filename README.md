# Government Schemes RAG Chatbot

![Vue.js](https://img.shields.io/badge/vue-%2335495e.svg?style=for-the-badge&logo=vuedotjs&logoColor=%234FC08D)
![Flask](https://img.shields.io/badge/flask-%23000.svg?style=for-the-badge&logo=flask&logoColor=white)
![Neo4j](https://img.shields.io/badge/Neo4j-008CC1?style=for-the-badge&logo=neo4j&logoColor=white)
![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)

A full-stack, voice-enabled Retrieval-Augmented Generation (RAG) chatbot designed to answer queries about Government Schemes. It leverages a **Local LLM** for natural language understanding, a **Neo4j Graph Database** for robust knowledge retrieval, and supports dual-language input/output in English and Marathi.

##  Features

- **Knowledge Graph RAG:** Uses Neo4j to store government scheme data, allowing for complex, relationship-based queries instead of standard vector similarity searches.
- **Local LLM Integration:** Translates user questions into precise Cypher queries to extract data directly from the knowledge graph.
- **Bilingual Support (English & Marathi):** - Translates Marathi text to English using `deep-translator` before processing.
  - Generates responses and reads them out aloud.
- **Voice-Enabled:** - **Speech-to-Text (STT):** Uses the browser's native Web Speech API.
  - **Text-to-Speech (TTS):** Uses Python's `pyttsx3` for offline voice synthesis.
- **Modern UI:** Built with Vue 3 and Tailwind CSS, featuring chat session management, responsive design, and local storage persistence.

---

##  Tech Stack

### Frontend
- **Framework:** Vue 3 + Vite
- **Styling:** Tailwind CSS
- **HTTP Client:** Axios
- **Speech Recognition:** Web Speech API

### Backend
- **Framework:** Python + Flask
- **Database:** Neo4j Graph Database
- **NLP & Translation:** `langdetect`, `deep-translator`
- **Text-to-Speech:** `pyttsx3`

---

##  Project Structure

```text
├── backend1/
│   ├── app.py                  # Main Flask application
│   ├── chatbot.py              # NLP, translation, and TTS logic
│   ├── cypher_generator.py     # Local LLM logic for generating Cypher queries
│   ├── graph_query.py          # Neo4j connection and query execution
│   ├── import_schemes.py       # Script to populate Neo4j from dataset.csv
│   ├── dataset.csv             # Government schemes dataset
│   └── examples.json           # Examples/Few-shot prompts for the LLM
│
└── frontend1/
    ├── src/
    │   ├── components/
    │   │   └── Chat.vue        # Main chat UI and logic
    │   ├── App.vue
    │   └── main.js
    ├── index.html
    ├── package.json
    ├── tailwind.config.js
    └── vite.config.js
```
 Getting Started
Prerequisites
Node.js (v16+)

Python 3.8+

Neo4j Desktop or Neo4j AuraDB

Local LLM setup (e.g., Ollama or a similar local inference server depending on your cypher_generator.py setup)

1. Database Setup (Neo4j)
Start your Neo4j instance.

Update the Neo4j credentials (URI, USERNAME, PASSWORD) in backend1/graph_query.py and backend1/import_schemes.py.

Run the import script to populate the graph with the schemes dataset:

Bash
cd backend1
python import_schemes.py
2. Backend Setup
Navigate to the backend directory:

Bash
cd backend1
Create and activate a virtual environment:

Bash
python -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate
Install the required Python packages (Ensure you have a requirements.txt or install manually):

Bash
pip install flask flask-cors neo4j deep-translator langdetect pyttsx3
Start the Flask server:

Bash
python app.py
The backend will run on http://127.0.0.1:5000.

3. Frontend Setup
Navigate to the frontend directory:

Bash
cd frontend1
Install Node.js dependencies:

Bash
npm install
Start the Vite development server:

Bash
npm run dev
The frontend will typically run on http://localhost:5173.

 How It Works
User Input: The user types or speaks a question in English or Marathi.

Translation: If the input is in Marathi, the Flask backend translates it to English.

Cypher Generation: The local LLM processes the English question and generates a Neo4j Cypher query.

Graph Execution: The Cypher query is executed against the Neo4j database to retrieve relevant scheme details.

Response: The data is formatted, returned to the frontend via JSON, and optionally spoken aloud using the TTS engine.

 Troubleshooting
Microphone Not Working: Ensure you are accessing the frontend via localhost or 127.0.0.1 (Browsers block microphone access on insecure non-local domains). Make sure your browser supports the Web Speech API.

Marathi Voice Recognition Issues: Make sure you explicitly select "Marathi" in the frontend dropdown before clicking the microphone icon.

Python TTS (pyttsx3) Crashing on Windows: If the Flask server crashes when trying to speak, ensure you have initialized pythoncom.CoInitialize() inside the background thread in chatbot.py.

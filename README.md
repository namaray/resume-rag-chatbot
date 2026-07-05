# 🤖 Interactive Resume RAG Chatbot

An AI-powered chatbot that answers questions about your resume, projects, and professional background using Retrieval-Augmented Generation (RAG). Built to impress recruiters and interviewers with a live, working demo of your AI/ML skills.

> **Answers are grounded in your real documents** — the chatbot will never fabricate skills, experiences, or claims.

## 🏗️ Architecture

```
┌──────────────────────┐     POST /api/chat     ┌─────────────────────────┐
│   Frontend           │ ──────────────────────► │   FastAPI Backend       │
│   HTML/CSS/JS        │ ◄────────────────────── │                         │
│   Standalone Chat UI │     JSON response       │   ┌─────────────────┐   │
└──────────────────────┘                         │   │ Embed Query     │   │
                                                 │   │ (Gemini)        │   │
                                                 │   └────────┬────────┘   │
                                                 │            ▼            │
                                                 │   ┌─────────────────┐   │
                                                 │   │ FAISS Search    │   │
                                                 │   │ (Top-K chunks)  │   │
                                                 │   └────────┬────────┘   │
                                                 │            ▼            │
                                                 │   ┌─────────────────┐   │
                                                 │   │ Generate Answer │   │
                                                 │   │ (Gemini Flash)  │   │
                                                 │   └─────────────────┘   │
                                                 └─────────────────────────┘
```

## 🛠️ Tech Stack

| Component | Technology |
|-----------|-----------|
| Backend | FastAPI (Python 3.11+) |
| Embeddings | Gemini `text-embedding-004` |
| Vector Store | FAISS (faiss-cpu) |
| LLM | Gemini 2.5 Flash |
| Frontend | HTML / CSS / Vanilla JS |
| Containerization | Docker |

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- A free Gemini API key from [Google AI Studio](https://aistudio.google.com/)

### 1. Setup

```bash
# Clone the repo
cd "Resume Chatbot"

# Create a virtual environment
cd backend
python -m venv venv

# Activate it
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure

```bash
# Copy the env template
cp .env.example .env

# Edit .env and add your Gemini API key
# GEMINI_API_KEY=your_key_here
```

### 3. Build the Index

```bash
python -m scripts.build_index
```

This reads your documents from `data/documents/`, chunks them, generates embeddings, and saves the FAISS index to `data/index/`.

### 4. Run the Backend

```bash
uvicorn app.main:app --reload --port 8000
```

The API is now running at `http://localhost:8000`. Visit `http://localhost:8000/docs` for the interactive API docs.

### 5. Open the Frontend

Open `frontend/index.html` in your browser. The chat UI will connect to the backend at `http://localhost:8000`.

## 📄 Customizing Your Documents

Replace the placeholder files in `backend/data/documents/` with your real content:

| File | Purpose |
|------|---------|
| `resume.md` | Your CV/resume |
| `projects.md` | Project descriptions |
| `bio.md` | Personal bio and summary |

You can add more `.md` files — the system will automatically pick them up.

After updating, rebuild the index:

```bash
python -m scripts.build_index
```

## 🐳 Docker Deployment

```bash
cd backend

# Build the image
docker build -t resume-chatbot .

# Run it
docker run -p 8000:8000 --env-file .env resume-chatbot
```

## 📁 Project Structure

```
Resume Chatbot/
├── backend/
│   ├── app/
│   │   ├── main.py          # FastAPI app & routes
│   │   ├── rag.py           # RAG pipeline
│   │   ├── embeddings.py    # Gemini embedding client
│   │   ├── vector_store.py  # FAISS index management
│   │   ├── chunker.py       # Document chunking
│   │   ├── config.py        # Settings
│   │   └── models.py        # Pydantic models
│   ├── data/
│   │   ├── documents/       # Your source documents
│   │   └── index/           # Built FAISS index
│   ├── scripts/
│   │   └── build_index.py   # Offline index builder
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env.example
├── frontend/
│   ├── index.html           # Chat page
│   ├── css/styles.css       # Premium dark theme
│   └── js/chat.js           # Chat logic
└── README.md
```

## 🔒 Anti-Hallucination Guardrails

- **Strict system prompt**: The LLM is instructed to answer ONLY from retrieved context
- **Retrieval gate**: Low-similarity results are filtered out before generation
- **Explicit refusal**: If no relevant context is found, the bot says so instead of guessing
- **Input filtering**: Basic prompt-injection patterns are blocked

## 📝 License

MIT

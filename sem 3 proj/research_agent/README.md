# Autonomous Research Agent

An AI agent that takes a research question, autonomously searches the web, reads sources, and synthesizes a comprehensive answer with citations.

## Features

- **Multi-step Research Loop**: Plans searches, scrapes sources, summarizes, evaluates completeness, and iterates
- **Multiple LLM Providers**: Groq (free), OpenAI, Google Gemini, Ollama (local)
- **Web Search & Scraping**: Uses DuckDuckGo for search, BeautifulSoup for content extraction
- **RAG Pipeline**: Vector storage with FAISS for document retrieval
- **Source Citations**: Every claim backed by traceable sources
- **Modern UI**: Beautiful Streamlit interface with real-time progress tracking
- **Research History**: Persistent session history with one-click recall

## Architecture

```
User Query → Planner → Search → Scrape → Summarize → Evaluate → (Loop) → Synthesize → Answer
```

## Quick Start

```bash
# Clone and navigate
cd research_agent

# Install dependencies
pip install -r requirements.txt

# Set up environment (choose ONE provider)
cp .env.example .env
# Edit .env with your API key

# Run
streamlit run app.py
```

## Provider Options

| Provider | Cost | Speed | Setup | Best For |
|----------|------|-------|-------|----------|
| **Groq** | Free (14k/day) | ⚡ Instant | API key only | **Recommended for demo** |
| **OpenAI** | Paid | Fast | API key | Production quality |
| **Gemini** | Free tier | Fast | API key | Google ecosystem |
| **Ollama** | Free (local) | Varies | Install + model pull | Privacy, offline |

### Groq (Recommended - Free & Fast)
1. Sign up at https://console.groq.com
2. Create API key
3. Add to `.env`: `GROQ_API_KEY=your-key`

### Ollama (Local, Private)
1. Install from https://ollama.com
2. Pull model: `ollama pull llama3.1`
3. Start server: `ollama serve`
4. Select "Ollama" in sidebar (no API key needed)

## Configuration

| Variable | Description | Required For |
|----------|-------------|--------------|
| `GROQ_API_KEY` | Groq API key | Groq |
| `OPENAI_API_KEY` | OpenAI API key | OpenAI |
| `GOOGLE_API_KEY` | Google AI Studio key | Gemini |
| `OLLAMA_BASE_URL` | Ollama server URL | Ollama (default: http://localhost:11434) |

## Usage

1. Select provider in sidebar (Groq recommended for free demo)
2. Enter API key if needed
3. Choose model variant
4. Adjust research depth (1-5 iterations)
5. Type research question
6. Click "Start Research"
7. View synthesized answer with sources

## Project Structure

```
research_agent/
├── app.py              # Streamlit UI with provider selection
├── research_agent.py   # Core agent logic (multi-provider)
├── requirements.txt    # Dependencies
├── .env.example        # Environment template
├── .env                # Your config (create from example)
└── __init__.py         # Package init
```

## Tech Stack

- **LLM Providers**: Groq, OpenAI, Google Gemini, Ollama (via LangChain)
- **Framework**: LangChain + LangGraph for agent orchestration
- **Search**: DuckDuckGo via `ddgs` (free, no API key)
- **Scraping**: BeautifulSoup4 + Requests
- **Embeddings**: sentence-transformers (local, free)
- **Vector Store**: FAISS
- **Frontend**: Streamlit with custom CSS

## Models by Provider

**Groq (Free & Fast)**:
- `openai/gpt-oss-20b` (default, ultra-fast & high TPM limit)
- `openai/gpt-oss-120b` (deep reasoning & high context)
- `qwen/qwen3.8-27b` (high-performance multilingual)

**OpenAI**:
- `gpt-4o-mini` (recommended)
- `gpt-4o` (best)
- `gpt-3.5-turbo` (cheapest)

**Ollama** (local):
- `llama3.1` (default)
- `llama3.1:70b` (larger)
- `mistral`, `qwen2.5`, `phi3`

**Gemini**:
- `gemini-1.5-flash` (free tier)
- `gemini-1.5-pro` (paid)

## License

MSc Semester 3 Project - Educational Use
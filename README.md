# Multi-Agent Research Team

Researches a topic on the web and writes a report using four LangGraph agents.

- **planner** – splits the topic into research questions
- **researcher** – searches DuckDuckGo and summarises results
- **writer** – drafts the report from the notes
- **critic** – scores the draft; below 8/10 it goes back to the writer (max 2 revisions)

Agents pass structured data using Pydantic models. Supports Groq, OpenAI, Gemini, Claude and Ollama.

## Setup

```
pip install -r requirements.txt
cp .env.example .env    # set LLM_PROVIDER and your API key
python main.py "how do lithium-ion batteries work"
```

Reports are saved to `reports/`.

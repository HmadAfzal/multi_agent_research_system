# Multi Agent Research system

A multi-agent research pipeline with a live status tracker. Enter a topic and four agents search the web, read a source, write a report, and review it.

**Live demo:** https://researchsystemmultiagent.streamlit.app/

## How It Works

The agents run in sequence:

1. **Search:** finds recent sources for the topic using Tavily (up to 5 results, each with title, URL, and snippet).
2. **Read:** picks the most relevant URL from the search results and scrapes its text.
3. **Draft:** writes a report from the search results and the scraped content. The report has an introduction, at least three key findings, a conclusion, and a list of sources.
4. **Critique:** reviews the draft and returns a score out of 10, strengths, areas to improve, and a one-line verdict.

The search and read steps are LangChain agents with one tool each. The draft and critique steps are LangChain prompt chains. All four use the `openai/gpt-oss-20b` model through Groq.

## Features

- Live tracker showing the four stages (active, done, error) and a timestamped log of each step
- Run history for the current session, with a sidebar to switch between runs or clear them
- Run stats: runtime, report word count, and feedback word count
- Four result tabs: Report, Critic feedback, Search results, and Scraped content
- Report download as Markdown or PDF
- Command-line mode, with no UI         

## Tech Stack

- [Streamlit](https://streamlit.io) for the UI
- [LangChain](https://www.langchain.com/) for agents and prompt chains
- [Groq](https://groq.com) for LLM inference
- [Tavily](https://tavily.com) for web search
- [Requests](https://requests.readthedocs.io/) and [Beautiful Soup](https://www.crummy.com/software/BeautifulSoup/) for scraping
- [ReportLab](https://www.reportlab.com/) for PDF generation

## Getting Started

### Prerequisites

- Python 3
- A [Groq](https://console.groq.com) API key
- A [Tavily](https://tavily.com) API key

### Installation

```bash
git clone https://github.com/HmadAfzal/multi_agent_research_system.git
cd multi_agent_research_system
pip install -r requirements.txt
```

### Configuration

Copy `.env.example` to `.env` and add your keys:

```env
GROQ_API_KEY=your-groq-api-key
TAVILY_API_KEY=your-tavily-api-key
```

### Run the app

```bash
streamlit run app.py
```

### Run from the command line

```bash
python pipeline.py
```

You will be prompted for a topic. Each stage prints its output to the terminal.

## Project Structure

```
app.py             Streamlit UI, live tracker, history, and PDF export
pipeline.py        Runs the four stages in order and reports progress
agents.py          Model setup, search and reader agents, writer and critic chains
tools.py           Web search (Tavily) and page scraping tools
requirements.txt   Python dependencies
.env.example       Template for API keys
.devcontainer/     Dev container configuration
```

## Limitations

- The reader agent scrapes one page per run.
- Scraped text is cut to the first 3,000 characters, and requests time out after 8 seconds.
- The reader agent chooses its URL from the first 800 characters of the search results.
- History is kept only for the current browser session.

## Deployment

The app is deployed on [Streamlit Community Cloud](https://share.streamlit.io) with `app.py` as the entry point. `GROQ_API_KEY` and `TAVILY_API_KEY` are set under the app's Secrets.

## License

This project is licensed under the [MIT License](LICENSE).

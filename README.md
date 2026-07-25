# Research Console
A multi-agent research pipeline with a live status tracker. </br>
**Live demo:** https://researchsystemmultiagent.streamlit.app/
## How it works
Give it a topic and four agents run in sequence:
1. **Search** — finds recent sources
2. **Read** — scrapes the best one
3. **Draft** — writes the report
4. **Critique** — reviews the draft
Each run is tracked live in the UI, kept in history for the session, and the final report can be downloaded as Markdown or PDF.
## Tech stack
- [Streamlit](https://streamlit.io) — UI
- [Groq](https://groq.com) — LLM inference
- [Tavily](https://tavily.com) — web search
- [ReportLab](https://www.reportlab.com/) — PDF generation
## Running locally
```bash
git clone https://github.com/HmadAfzal/multi_agent_research_system/
cd multi_agent_research_system
pip install -r requirements.txt
```
Create `.streamlit/secrets.toml`:
```toml
GROQ_API_KEY = "your-groq-api-key-here"
TAVILY_API_KEY = "your-tavily-api-key-here"
```
Then run:
```bash
streamlit run app.py
```
## Deployment
Deployed on [Streamlit Community Cloud](https://share.streamlit.io), pointed at `app.py`, with `GROQ_API_KEY` and `TAVILY_API_KEY` set under the app's Secrets.

---
Note: UI created by Claude Sonnet 5, effort: high.
# Single-Agent Deep Market Research - Implementation Plan

> **For AI Agent Workers:** Prioritize using `executing-plans` to implement this plan task by task. Use checkbox (`- [ ]`) syntax to track progress.

**Goal:** Replace the 10-agent CrewAI crew with a single CrewAI agent equipped with specialized tools (batch search, page visitor with Jina reader + LLM extraction, website scraper) that uses the full market research MD prompt as its methodology. This reduces token usage ~5x while improving research quality by actually reading web pages instead of relying on search snippets.

**Architecture:** A single CrewAI Agent with a ReAct-style execution loop. The agent receives the full market research methodology (from `comprehensive Market Research.md`) as its goal, and has access to 4 specialized tools: `batch_search` (Exa API, multiple queries in one call), `visit_page` (Jina reader fetches full page content + LLM extracts relevant info), `scrape_website` (for brand's own website), and `save_report` (writes final report to `output/` folder). The agent adaptively decides what to search and which pages to visit based on findings, just like DeepResearch's ReAct loop.

**Tech Stack:**
- CrewAI (agent framework, already installed)
- Exa API (web search, API key already in `.env`)
- Jina AI Reader API (free tier, reads full web pages)
- Ollama Cloud (LLM, already configured in `.env`)
- Python `requests` library (for Jina API calls)
- `tiktoken` (for token truncation, prevents context overflow)

---

## File Structure

| File | Responsibility | Source |
|------|---------------|--------|
| `tools/__init__.py` | Package init, exports all tools | New |
| `tools/batch_search.py` | Exa batch search tool (multiple queries in one call) | Adapted from DeepResearch's `tool_search.py` + CrewAI tool pattern |
| `tools/visit_page.py` | Jina reader + LLM extraction (reads full page, summarizes relevant info) | Adapted from DeepResearch's `tool_visit.py` |
| `tools/scrape_website.py` | Thin wrapper re-exporting `ScrapeWebsiteTool` from crewai_tools | Existing |
| `tools/save_report.py` | Custom tool that writes report content to `output/` folder | New |
| `market_research_crew.py` | Main entry point: single agent + single task + crew orchestration + CLI | Rewrite of existing file |
| `prompts.py` | The full market research methodology prompt (extracted from MD file) | New, extracted from `comprehensive Market Research.md` |
| `requirements.txt` | Updated dependencies (adds `requests`, `tiktoken`) | Modify existing `pyproject.toml` |
| `.env.example` | Updated with Jina API key placeholder | Modify existing |

---

## Task 1: Create Batch Search Tool

**Files:**
- Create: `tools/__init__.py`
- Create: `tools/batch_search.py`

**Prerequisites:**
- None

**Completion Criteria:**
- `BatchSearchTool` class exists as a CrewAI `BaseTool` subclass
- Tool accepts a list of search queries and returns formatted results
- Uses Exa API (key from `EXA_API_KEY` env var)
- Each result includes title, URL, snippet, and published date
- Tool is importable: `from tools.batch_search import BatchSearchTool`

- [ ] **Step 1: Create `tools/__init__.py`**

```python
from tools.batch_search import BatchSearchTool
from tools.visit_page import VisitPageTool
from tools.save_report import SaveReportTool
```

- [ ] **Step 2: Create `tools/batch_search.py`**

Adapt DeepResearch's batch search pattern ([tool_search.py#L113-L129](file:///C:/Users/lee/Desktop/DeepResearch-main/inference/tool_search.py)) into a CrewAI `BaseTool`.

Key design decisions:
- Use Exa API (already has key) instead of Serper (DeepResearch's choice)
- Accept a Python list of query strings (not JSON array) for CrewAI compatibility
- Return formatted markdown with numbered results, titles as clickable links
- Truncate each result snippet to 500 chars to control token usage

```python
from crewai.tools import BaseTool
from exa_py import Exa
import os

class BatchSearchTool(BaseTool):
    name: str = "batch_search"
    description: str = (
        "Search the web for multiple queries at once. "
        "Pass a list of search query strings. Returns top 5 results per query "
        "with title, URL, snippet, and date. Use this for broad research."
    )

    def _run(self, queries: list) -> str:
        exa = Exa(api_key=os.getenv("EXA_API_KEY"))
        results = []

        if isinstance(queries, str):
            queries = [queries]

        for query in queries:
            try:
                response = exa.search_and_contents(
                    query,
                    num_results=5,
                    use_autoprompt=True,
                    text=True,
                    highlights=True
                )
                formatted = f"## Search: '{query}'\n"
                for i, result in enumerate(response.results, 1):
                    snippet = (result.text or "")[:500]
                    date = getattr(result, 'published_date', '') or ''
                    formatted += f"{i}. [{result.title}]({result.url})"
                    if date:
                        formatted += f" ({date})"
                    formatted += f"\n   {snippet}\n\n"
                results.append(formatted)
            except Exception as e:
                results.append(f"## Search: '{query}'\nError: {str(e)}\n")

        return "\n---\n".join(results)
```

- [ ] **Step 3: Verify import works**

Run: `uv run python -c "from tools.batch_search import BatchSearchTool; print('OK')"`
Expected: `OK`

---

## Task 2: Create Visit Page Tool (Jina Reader + LLM Extraction)

**Files:**
- Create: `tools/visit_page.py`

**Prerequisites:**
- Task 1 complete

**Completion Criteria:**
- `VisitPageTool` class exists as a CrewAI `BaseTool` subclass
- Tool fetches full page content via Jina Reader API (`https://r.jina.ai/{url}`)
- LLM extracts only relevant info using the extraction prompt from DeepResearch
- Page content is truncated to 95K tokens before extraction (prevents context overflow)
- Tool accepts a URL (or list of URLs) and a research goal
- Returns structured output: evidence + summary (not raw page content)
- Works without Jina API key (free tier) but uses key if available

- [ ] **Step 1: Create `tools/visit_page.py`**

Adapt DeepResearch's visit tool ([tool_visit.py](file:///C:/Users/lee/Desktop/DeepResearch-main/inference/tool_visit.py)) into a CrewAI `BaseTool`.

Key design decisions:
- Use Jina Reader API (`https://r.jina.ai/{url}`) — free tier works without API key
- Use the LLM (passed via env var or CrewAI's default) to extract relevant info
- Use DeepResearch's [EXTRACTOR_PROMPT](file:///C:/Users/lee/Desktop/DeepResearch-main/inference/prompt.py#L37-L51) for the extraction prompt
- Truncate to 95K tokens using `tiktoken` (same as DeepResearch)
- For multiple URLs, visit each one and concatenate results
- If Jina fails, return error message (don't crash)

```python
from crewai.tools import BaseTool
import requests
import os
import json
from openai import OpenAI

EXTRACTOR_PROMPT = """Please process the following webpage content and user goal to extract relevant information:

## Webpage Content
{webpage_content}

## User Goal
{goal}

## Task Guidelines
1. Locate the specific sections/data directly related to the user's goal
2. Extract the most relevant information, output the full original context, can be multiple paragraphs
3. Organize into a concise summary with logical flow

Output as JSON with fields: "evidence" and "summary"
"""

def truncate_to_tokens(text, max_tokens=95000):
    try:
        import tiktoken
        encoding = tiktoken.get_encoding("cl100k_base")
        tokens = encoding.encode(text)
        if len(tokens) <= max_tokens:
            return text
        return encoding.decode(tokens[:max_tokens])
    except:
        return text[:max_tokens * 4]  # fallback: ~4 chars per token


class VisitPageTool(BaseTool):
    name: str = "visit_page"
    description: str = (
        "Visit webpage(s) and get a summary of relevant content. "
        "Pass a URL (or list of URLs) and a research goal describing what you want to learn. "
        "Returns extracted evidence and a summary — not the raw full page."
    )

    def _run(self, url, goal: str = "") -> str:
        if isinstance(url, str):
            urls = [url]
        else:
            urls = url

        results = []
        for u in urls:
            content = self._fetch_page(u)
            if not content or content.startswith("[visit] Failed"):
                results.append(f"URL: {u}\nFailed to read page.\n")
                continue

            content = truncate_to_tokens(content, max_tokens=95000)
            extracted = self._extract_info(content, goal, u)
            results.append(extracted)

        return "\n---\n".join(results)

    def _fetch_page(self, url: str) -> str:
        jina_key = os.getenv("JINA_API_KEY", "")
        headers = {}
        if jina_key:
            headers["Authorization"] = f"Bearer {jina_key}"

        try:
            response = requests.get(
                f"https://r.jina.ai/{url}",
                headers=headers,
                timeout=30
            )
            if response.status_code == 200:
                return response.text
            return f"[visit] Failed: HTTP {response.status_code}"
        except Exception as e:
            return f"[visit] Failed: {str(e)}"

    def _extract_info(self, content: str, goal: str, url: str) -> str:
        # Use Ollama Cloud or OpenAI for extraction
        api_key = os.getenv("OLLAMA_API_KEY", "")
        base_url = os.getenv("LLM_BASE_URL", "https://ollama.com/v1")
        model = os.getenv("EXTRACTION_MODEL", "gpt-oss:20b-cloud")

        try:
            client = OpenAI(api_key=api_key, base_url=base_url)
            prompt = EXTRACTOR_PROMPT.format(webpage_content=content, goal=goal)
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3
            )
            raw = response.choices[0].message.content

            # Try to parse JSON
            try:
                raw = raw.replace("```json", "").replace("```", "").strip()
                parsed = json.loads(raw)
                evidence = parsed.get("evidence", raw)
                summary = parsed.get("summary", "")
            except:
                evidence = raw
                summary = ""

            return f"URL: {url}\nEvidence: {evidence}\nSummary: {summary}\n"
        except Exception as e:
            # Fallback: return truncated raw content
            return f"URL: {url}\nContent (truncated): {content[:2000]}\n[Extraction failed: {str(e)}]\n"
```

- [ ] **Step 2: Install tiktoken dependency**

Run: `uv add tiktoken`

- [ ] **Step 3: Verify import works**

Run: `uv run python -c "from tools.visit_page import VisitPageTool; print('OK')"`
Expected: `OK`

---

## Task 3: Create Save Report Tool

**Files:**
- Create: `tools/save_report.py`

**Prerequisites:**
- None

**Completion Criteria:**
- `SaveReportTool` class exists as a CrewAI `BaseTool` subclass
- Tool accepts report content and a filename
- Writes to `output/` directory (creates if not exists)
- Returns confirmation message with file path
- Filename is sanitized (no special characters)

- [ ] **Step 1: Create `tools/save_report.py`**

```python
from crewai.tools import BaseTool
import os
import re

class SaveReportTool(BaseTool):
    name: str = "save_report"
    description: str = (
        "Save the market research report to a markdown file. "
        "Pass the full report content and a brand name for the filename. "
        "The file will be saved in the output/ folder."
    )

    def _run(self, content: str, brand_name: str = "report") -> str:
        output_dir = os.path.join(os.getcwd(), "output")
        os.makedirs(output_dir, exist_ok=True)

        safe_name = re.sub(r'[^a-zA-Z0-9_-]', '_', brand_name)
        filename = f"{safe_name}_market_research.md"
        filepath = os.path.join(output_dir, filename)

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)

        return f"Report saved to: {filepath}"
```

- [ ] **Step 2: Verify import works**

Run: `uv run python -c "from tools.save_report import SaveReportTool; print('OK')"`
Expected: `OK`

---

## Task 4: Extract Market Research Prompt

**Files:**
- Create: `prompts.py`

**Prerequisites:**
- None

**Completion Criteria:**
- `MARKET_RESEARCH_PROMPT` constant contains the full methodology from `comprehensive Market Research.md`
- Prompt includes all 9 steps with their full detail
- Prompt includes all "THROUGHOUT ALL RESEARCH" deliverables
- Prompt includes all "FINAL DOCUMENT WILL ANSWER" questions
- Prompt includes the 5 ad concept structure (14 fields each)
- Prompt includes the FINAL ANALYSIS section
- Prompt uses `{brand_website}` and `{product_info}` placeholders for variable injection
- Continuation instructions are removed (not needed for agent — agent handles this natively)

- [ ] **Step 1: Create `prompts.py`**

Extract the full methodology from [comprehensive Market Research.md](file:///C:/Users/lee/Desktop/test-agent/comprehensive%20Market%20Research.md) into a Python string constant.

Key extraction decisions:
- Remove the "ask me for the brand's website" intro (the agent receives this via task inputs)
- Remove the "HANDLING CONTINUATIONS" section (CrewAI agent doesn't need this)
- Keep ALL 9 steps with their full detail
- Keep ALL deliverables, questions, ad concept structure, and final analysis
- Add `{brand_website}` and `{product_info}` placeholders where the brand info goes
- Add tool usage guidance at the top (tell the agent to use `batch_search`, `visit_page`, etc.)

The prompt structure should be:

```python
MARKET_RESEARCH_PROMPT = """You are conducting an in-depth market research for: {brand_website}

Additional product info: {product_info}

## TOOL USAGE GUIDELINES
- Use batch_search to find information across the web (multiple queries at once)
- Use visit_page to read full content of important pages (competitor sites, Reddit threads, review pages)
- Use scrape_website to read the brand's own website
- Use save_report to save your final report

## RESEARCH METHODOLOGY

[... full content of all 9 steps from the MD file ...]

## THROUGHOUT ALL RESEARCH — DOCUMENT THESE
[... all deliverables ...]

## FINAL DOCUMENT WILL ANSWER
[... all questions ...]

## AD CONCEPT RECOMMENDATIONS
[... 5 concepts, 14 fields each ...]

## FINAL ANALYSIS
[... 5 sections ...]
"""
```

- [ ] **Step 2: Verify prompt loads**

Run: `uv run python -c "from prompts import MARKET_RESEARCH_PROMPT; print(len(MARKET_RESEARCH_PROMPT), 'chars')"`
Expected: `> 5000 chars`

---

## Task 5: Rewrite `market_research_crew.py` as Single Agent

**Files:**
- Modify: `market_research_crew.py` (complete rewrite)

**Prerequisites:**
- Tasks 1, 2, 3, 4 complete

**Completion Criteria:**
- File contains ONE agent (not 10)
- Agent has 4 tools: `batch_search`, `visit_page`, `scrape_website`, `save_report`
- Agent's goal is the full `MARKET_RESEARCH_PROMPT` from `prompts.py`
- ONE task assigns the research to the agent
- Crew has 1 agent, 1 task, `Process.sequential`
- CLI interface preserved (accepts input file or interactive mode)
- Output is saved to `output/` folder (via tool AND via `run_market_research` function)
- LLM configuration preserved (Ollama Cloud / OpenAI switch)
- `.env` loading preserved

- [ ] **Step 1: Rewrite `market_research_crew.py`**

Replace the entire file with the single-agent architecture:

```python
from crewai import Agent, Task, Crew, Process, LLM
from crewai_tools import ScrapeWebsiteTool
from tools.batch_search import BatchSearchTool
from tools.visit_page import VisitPageTool
from tools.save_report import SaveReportTool
from prompts import MARKET_RESEARCH_PROMPT
import os
import re
from dotenv import load_dotenv

load_dotenv()

# Tool initialization
batch_search = BatchSearchTool()
visit_page = VisitPageTool()
scrape_website = ScrapeWebsiteTool()
save_report = SaveReportTool()

# LLM configuration (unchanged from current)
llm_provider = os.getenv("LLM_PROVIDER", "ollama_cloud").lower()

if llm_provider == "ollama_cloud":
    llm = LLM(
        model="openai/gpt-oss:20b-cloud",
        temperature=0.7,
        base_url="https://ollama.com/v1",
        api_key=os.getenv("OLLAMA_API_KEY")
    )
    print("Using Ollama Cloud (gpt-oss:20b-cloud)")
elif llm_provider == "openai":
    llm = LLM(
        model="openai/gpt-4o-mini",
        temperature=0.7,
        api_key=os.getenv("OPENAI_API_KEY")
    )
    print("Using OpenAI LLM")

# Single agent
market_researcher = Agent(
    role="Deep Market Research Analyst",
    goal=MARKET_RESEARCH_PROMPT,
    backstory=(
        "You are an elite market researcher with 20+ years of experience in "
        "consumer psychology, competitive analysis, and advertising strategy. "
        "You conduct thorough multi-source investigations, visiting websites, "
        "reading reviews, analyzing Reddit discussions, and studying social media. "
        "You think strategically about positioning, desires, and market sophistication."
    ),
    tools=[batch_search, visit_page, scrape_website, save_report],
    verbose=True,
    allow_delegation=False,
    llm=llm,
    max_iter=25  # Allow up to 25 tool calls
)

# Single task
research_task = Task(
    description=MARKET_RESEARCH_PROMPT,
    expected_output=(
        "A comprehensive 25+ page market research document with all 9 steps completed, "
        "including Top 30 desires, Top 30 problems, 5 ad concepts with 14 fields each, "
        "and a full strategic analysis. Save the report using the save_report tool."
    ),
    agent=market_researcher,
)

# Single-agent crew
market_research_crew = Crew(
    agents=[market_researcher],
    tasks=[research_task],
    process=Process.sequential,
    verbose=True,
)

def run_market_research(brand_website, product_info=""):
    # ... preserved from current implementation ...
    # Calls kickoff(), saves output to output/ folder

def parse_input_file(filepath):
    # ... preserved from current implementation ...

if __name__ == "__main__":
    # ... preserved CLI interface ...
```

- [ ] **Step 2: Verify syntax**

Run: `uv run python -c "import ast; ast.parse(open('market_research_crew.py', encoding='utf-8').read()); print('Syntax OK')"`
Expected: `Syntax OK`

- [ ] **Step 3: Verify imports**

Run: `uv run python -c "from market_research_crew import market_research_crew; print('Import OK')"`
Expected: `Using Ollama Cloud...` + `Import OK`

---

## Task 6: Update Dependencies and Config

**Files:**
- Modify: `pyproject.toml`
- Modify: `.env.example`
- Modify: `.env` (add Jina key placeholder)

**Prerequisites:**
- Tasks 1-5 complete

**Completion Criteria:**
- `pyproject.toml` includes `tiktoken` and `requests` (if not already)
- `langchain-openai` removed (no longer used)
- `.env.example` includes `JINA_API_KEY` (optional, free tier works without it)
- `.env` updated with `JINA_API_KEY=` (empty, free tier)

- [ ] **Step 1: Update `pyproject.toml`**

Ensure dependencies include:
```toml
dependencies = [
    "crewai[tools]>=1.15.1",
    "exa-py>=2.16.0",
    "python-dotenv>=1.0.0",
    "tiktoken>=0.7.0",
    "requests>=2.31.0",
]
```

- [ ] **Step 2: Update `.env.example`**

Add:
```env
# Jina Reader API (optional - free tier works without key)
# Get yours at: https://jina.ai/
JINA_API_KEY=
```

- [ ] **Step 3: Update `.env`**

Add `JINA_API_KEY=` line (empty for free tier)

- [ ] **Step 4: Run `uv sync` to install new deps**

Run: `uv sync`
Expected: `Resolved N packages` with no errors

---

## Task 7: Test Run and Validate

**Files:**
- None (testing only)

**Prerequisites:**
- Tasks 1-6 complete

**Completion Criteria:**
- Crew runs with `input/example_course.txt` without import errors
- Agent makes at least 3 `batch_search` calls
- Agent makes at least 2 `visit_page` calls
- Agent uses `save_report` tool to save output
- Report file appears in `output/` folder
- Report contains at least: brand analysis, competitor research, and one ad concept
- No crashes or unhandled exceptions

- [ ] **Step 1: Run the crew**

Run: `$env:PYTHONIOENCODING="utf-8"; uv run python market_research_crew.py input/example_course.txt`

- [ ] **Step 2: Monitor agent behavior**

Check that the agent:
- Searches for ShipFast
- Visits shipfast.com
- Searches for competitors
- Visits competitor pages
- Searches for Reddit discussions
- Saves the report

- [ ] **Step 3: Verify output file exists**

Run: `Get-ChildItem output/`
Expected: At least one `.md` file

- [ ] **Step 4: Verify report content**

Read the output file and confirm it contains:
- Brand analysis section
- Competitor research section
- At least partial ad concepts
- Source links in markdown format

- [ ] **Step 5: Commit**

```powershell
git add tools/ prompts.py market_research_crew.py pyproject.toml .env.example docs/
git commit -m "feat: replace 10-agent crew with single-agent multi-tool architecture

- Single CrewAI agent with 4 specialized tools (batch_search, visit_page, scrape_website, save_report)
- Adapted DeepResearch's Jina reader + LLM extraction for page visits
- Full market research methodology preserved in prompts.py
- ~5x token reduction vs 10-agent approach"
```

---

## Token Usage Comparison (Expected)

| Approach | Agents | Tool Calls | Context Compounding | Estimated Tokens |
|----------|--------|-----------|---------------------|-----------------|
| Old (10 agents) | 10 | ~30 | Yes (each agent reads all previous) | ~150K |
| New (1 agent) | 1 | ~20-25 | No (summarized pages only) | ~30-40K |

---

## Key Design Decisions

1. **Why not use DeepResearch's ReAct loop directly?** — DeepResearch requires a vLLM server and Qwen agent framework. Too heavy. CrewAI already provides the ReAct loop via `max_iter`.

2. **Why Jina Reader instead of ScrapeWebsiteTool?** — Jina reads JavaScript-rendered pages, returns clean markdown, and handles dynamic content. `ScrapeWebsiteTool` is basic HTML scraping.

3. **Why LLM extraction on visited pages?** — Raw page content can be 100K+ tokens. Extracting only relevant info reduces context by ~80%. This is the key insight from DeepResearch.

4. **Why `max_iter=25`?** — DeepResearch allows up to 100 LLM calls. We use 25 as a balance between thoroughness and token budget. Each iter = 1 tool call + 1 LLM reasoning step.

5. **Why keep `scrape_website` tool?** — For the brand's own website, we want full content (not summarized). `ScrapeWebsiteTool` gives us raw HTML/text for the brand site, while `visit_page` (Jina + extraction) is for competitor/research pages where we want summaries.

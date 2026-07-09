# Market Research Agent

Generate a comprehensive market research report for any brand or product — competitive landscape, customer desires, Amazon/Reddit quotes, ad angles, and a strategic roadmap. One CrewAI agent with 4 tools, ~35K tokens per run.

## Quick Start

```bash
# 1. Install
git clone https://github.com/shipblueprint/deep-market-research-agent.git
cd deep-market-research-agent
uv sync

# 2. Add your API keys (see below)
cp .env.example .env
# Edit .env in any text editor

# 3. Run on an example
python market_research_crew.py input/example_saas.txt
```

The script takes 2-5 minutes (visits 20+ pages, 6 research phases). Results land in `output/`.

---

## Prerequisites

| Thing | Required? | Get it |
|-------|-----------|--------|
| **Python 3.11+** | ✅ | `python3 --version` |
| **uv** (package manager) | ✅ | `curl -LsSf https://astral.sh/uv/install.sh \| sh` |
| **Exa API key** | ✅ | [exa.ai](https://exa.ai) — free tier: 1,000 searches/month |
| **Ollama Cloud key** or **OpenAI key** | ✅ (pick one) | [Ollama Cloud free tier](https://ollama.com/settings/keys) or [OpenAI](https://platform.openai.com/api-keys) |
| **Jina Reader key** | ❌ (optional) | [jina.ai](https://jina.ai/) — free unauthenticated tier works |

---

## 1. API Keys (where to put them)

Copy the template and fill in your keys:

```bash
cp .env.example .env
```

Open `.env` in any text editor. It should look like this:

```env
# Which LLM to use: "ollama_cloud" or "openai"
LLM_PROVIDER=ollama_cloud

# Ollama Cloud (free tier: https://ollama.com/settings/keys)
OLLAMA_API_KEY=ok-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Exa Search (free tier: https://exa.ai)
EXA_API_KEY=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx

# OpenAI (only if LLM_PROVIDER=openai)
# OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Jina Reader (optional — free unauthenticated tier works without a key)
# JINA_API_KEY=jina_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

**Only two keys are mandatory:** Exa API key + one LLM key (Ollama Cloud or OpenAI).

---

## 2. Run

### Use an example input file (easiest)

```bash
python market_research_crew.py input/example_saas.txt
```

Replace `example_saas.txt` with:

| File | Brand | Category |
|------|-------|----------|
| `example_saas.txt` | Notion | SaaS / Productivity |
| `example_ecommerce.txt` | Liquid I.V. | E-commerce / Beverage |
| `example_fitness.txt` | MacroFactor | App / Fitness |
| `example_course.txt` | ShipFast | Developer tool / Boilerplate |
| `example_supplement.txt` | AG1 | Supplement / Health |

### Interactive mode

```bash
python market_research_crew.py
```

It'll prompt you for a brand URL and product description, or let you pick from the examples.

### Research your own brand

Create a `.txt` file in `input/`:

```
website: https://your-brand.com
product: Brief description of the product, target audience, and key value proposition.
```

Then run:

```bash
python market_research_crew.py input/your-file.txt
```

### Windows users

Replace `cp` with `copy` in PowerShell, and use `python` the same way:

```powershell
copy .env.example .env
python market_research_crew.py input/example_saas.txt
```

---

## What you get

The report in `output/` covers:

- **Brand positioning** — how the brand presents itself
- **Customer desire mapping** — what customers actually want, with direct quotes
- **Competitor landscape** — 10-15 competitors with source links
- **Customer voice** — 40+ Amazon review quotes + 50+ Reddit quotes
- **Market analysis** — social media hooks, market sophistication, ad style
- **Ad concepts** — 3+ campaign angles with rationale
- **Strategic roadmap** — recommended next steps

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `ModuleNotFoundError: No module named 'prompts'` | Run `cp prompts.example/*.py prompts/` — the prompts/ directory is gitignored and needs to be created on first clone |
| `No brand website provided` | Make sure your input file starts with `website: https://...` |
| `API key errors` | Check `.env` keys are correct and `.env` is in the project root |
| `Rate limited (Ollama free tier)` | Free tier has session limits. Wait or switch to `LLM_PROVIDER=openai` |
| Agent running slowly | Expected — it visits 20+ pages across 6 phases. Check console for progress |
| `uv: command not found` | Install uv: `curl -LsSf https://astral.sh/uv/install.sh \| sh` |

---

## How it works (for the curious)

A **single CrewAI agent** runs 6 research phases sequentially. Between phases it uses its tools:

| Phase | What happens |
|-------|-------------|
| 1. Brand Analysis | Scrapes brand website, runs search queries |
| 2. Desire Mapping | Searches customer pain points, visits pages |
| 3. Competitor Research | Searches competitors, visits their sites |
| 4. Community Research | Searches Reddit + Amazon for authentic quotes |
| 5. Market Analysis | Analyzes social media, sophistication, ad styles |
| 6. Final Report | Compiles everything into a report |

### Why single-agent instead of 10 agents?

| 10-agent crew | Single-agent + tools |
|---|---|
| Each agent re-reads the same context → ~5x tokens | One agent holds context once, tools fetch on demand |
| Tools duplicated across all agents | Tools owned by one agent, used when needed |
| Hard to debug which agent failed | Single linear trace |
| ~150K tokens per run | ~35K tokens per run |

### Tools

| Tool | What it does | How |
|------|-------------|-----|
| `batch_search` | Runs 5-10 Exa searches in one call | Exa API |
| `visit_page` | Fetches URL, extracts relevant info | Jina Reader + LLM summarization |
| `scrape_website` | Full website scrape | CrewAI built-in |
| `save_report` | Writes report to `output/` | Local file |

---

## Customizing prompts

Research methodology lives in `prompts/` — one file per phase. Edit them to change what the agent researches.

### First time setup

```bash
# prompts/ is gitignored — copy the example templates
cp prompts.example/*.py prompts/
```

### File layout

```
prompts/
├── __init__.py              # Exports all prompts
├── system_prompt.py         # Agent goal + tool usage rules
├── brand_analysis.py        # Phase 1
├── desire_mapping.py         # Phase 2
├── competitor_research.py    # Phases 3-4
├── community_research.py     # Phases 5-6
├── market_analysis.py        # Phases 7-9
└── final_report.py           # Phase 10
```

Each file exports one constant (e.g., `BRAND_ANALYSIS_PROMPT`). Two placeholders are available:

- `{brand_website}` — replaced with the URL from your input file
- `{product_info}` — replaced with the product description

### Writing tips

- **Be specific** — "List 10-15 competitors" beats "List competitors"
- **Request quotes with links** — forces the agent to use tools instead of guessing
- **Map each phase to a tool** — mention which searches to run (e.g., `site:reddit.com {brand}`)

### Keeping prompts private

`prompts/` is gitignored by default. Your custom methodology stays local. The `prompts.example/` directory contains generic templates safe to commit.

---

## Project structure

```
├── market_research_crew.py    # Agent, tasks, crew, CLI
├── prompts/                   # Research methodology (gitignored)
├── prompts.example/           # Public templates
├── tools/
│   ├── batch_search.py        # Exa batch search
│   ├── visit_page.py          # Jina Reader + LLM extraction
│   └── save_report.py         # File output
├── input/                     # Example input files
├── output/                    # Generated reports (gitignored)
├── .env                       # API keys (gitignored)
├── .env.example               # API key template
├── pyproject.toml             # Dependencies
└── README.md
```

## LLM provider details

### Ollama Cloud (default, free tier)

```env
LLM_PROVIDER=ollama_cloud
OLLAMA_API_KEY=ok-...
```

- Default model: `gpt-oss:20b-cloud` (free, good for testing)
- Upgrade: `gpt-oss:120b-cloud` (edit model name in `market_research_crew.py`)
- Limits: 1 concurrent model, session + weekly caps

### OpenAI (paid)

```env
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-...
```

- Model: `gpt-4o-mini`
- Best quality, no rate limits, costs money

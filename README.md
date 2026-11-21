[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE) ![GitHub release](https://img.shields.io/github/v/release/shipschematic/agent-deep-market-research)

# Market Research Agent

Generate a comprehensive market research report for any brand or product: competitive landscape, customer desires, Amazon/Reddit quotes, ad angles, and a strategic roadmap. One CrewAI agent with four tools.

## Quick Start

```bash
# 1. Install
git clone https://github.com/shipschematic/agent-deep-market-research.git
cd agent-deep-market-research
uv sync

# 2. Add your API keys (see below)
cp .env.example .env
# Edit .env in any text editor

# 3. Run on an example
uv run python market_research_crew.py input/example_saas.txt
```

The first run creates `prompts/` from `prompts.example/` automatically. The script takes 2-5 minutes: it visits 20+ pages across 6 research phases. Results land in `output/`.

---

## Prerequisites

| Thing | Required? | Get it |
|-------|-----------|--------|
| **Python 3.11.5+** | ✅ | `python3 --version` |
| **uv** (package manager) | ✅ | `curl -LsSf https://astral.sh/uv/install.sh \| sh` |
| **Exa API key** | ✅ | [exa.ai](https://exa.ai) — free tier: 1,000 searches/month |
| **Ollama Cloud key** or **OpenAI key** | ✅ (pick one) | [Ollama Cloud free tier](https://ollama.com/settings/keys) or [OpenAI](https://platform.openai.com/api-keys) |
| **Jina Reader key** | ❌ (optional) | [jina.ai](https://jina.ai/) — free unauthenticated tier works |

---

## 1. API Keys

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

**Only two keys are mandatory:** Exa API key plus one LLM key (Ollama Cloud or OpenAI).

Check the setup without spending tokens:

```bash
uv run python market_research_crew.py --check
```

---

## 2. Run

### Use an example input file (easiest)

```bash
uv run python market_research_crew.py input/example_saas.txt
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
uv run python market_research_crew.py
```

It prompts for a brand URL and product description, or lets you pick from the examples.

### Research your own brand

Create a `.txt` file in `input/`:

```
website: https://your-brand.com
product: Brief description of the product, target audience, and key value proposition.
```

Then run:

```bash
uv run python market_research_crew.py input/your-file.txt
```

### Windows users

Replace `cp` with `copy` in PowerShell. `uv run` works the same way:

```powershell
copy .env.example .env
uv run python market_research_crew.py input/example_saas.txt
```

---

## What you get

The report in `output/` covers:

- **Brand positioning** — how the brand presents itself
- **Customer desire mapping** — what customers actually want, with direct quotes
- **Competitor landscape** — competitors with source links
- **Customer voice** — Amazon review and Reddit quotes with links
- **Market analysis** — social media hooks, market sophistication, ad style
- **Ad concepts** — campaign angles with rationale
- **Strategic roadmap** — recommended next steps

Reports are named `<brand>_market_research.md`. Treat quotes and statistics as leads until the linked source is checked.

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `ModuleNotFoundError: No module named 'prompts'` | Run from the project root. `prompts/` is created automatically on first run; if it is missing, run `cp prompts.example/*.py prompts/` |
| `Missing required environment variables` | Add the named keys to `.env` in the project root |
| `Unsupported LLM_PROVIDER` | Set `LLM_PROVIDER` to `ollama_cloud` or `openai` |
| `No brand website provided` | Make sure your input file starts with `website: https://...` |
| `Rate limited (Ollama free tier)` | Free tier has session limits. Wait or switch to `LLM_PROVIDER=openai` |
| `No report file found in output/` | The agent did not call `save_report`. Re-run the final phase or check the console trace |
| Agent running slowly | Expected — it visits 20+ pages across 6 phases. Check console progress |
| `uv: command not found` | Install uv: `curl -LsSf https://astral.sh/uv/install.sh \| sh` |

---

## How it works

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
| Each agent re-reads the same context | One agent holds context once, tools fetch on demand |
| Tools duplicated across all agents | Tools owned by one agent, used when needed |
| Hard to debug which agent failed | Single linear trace |
| Higher token use | Lower token use |

### Tools

| Tool | What it does | How |
|------|-------------|-----|
| `batch_search` | Runs 5-10 Exa searches in one call | Exa API |
| `visit_page` | Fetches URL, extracts relevant info | Jina Reader + LLM summarization |
| `scrape_website` | Full website scrape | CrewAI built-in |
| `save_report` | Writes report to `output/` | Local file |

Page extraction uses the same provider as the main model. `LLM_PROVIDER=openai` uses `OPENAI_API_KEY`; `LLM_PROVIDER=ollama_cloud` uses `OLLAMA_API_KEY`.

---

## Customizing prompts

Research methodology lives in `prompts/` — one file per phase. Edit them to change what the agent researches.

### First time setup

`prompts/` is gitignored. The first run copies the templates automatically:

```bash
uv run python market_research_crew.py input/example_saas.txt
# Created prompts/ from prompts.example/
```

To reset your local copy:

```bash
rm -rf prompts/
uv run python market_research_crew.py --check
```

### File layout

```
prompts/
├── __init__.py              # Exports all prompts
├── system_prompt.py         # Agent goal + tool usage rules
├── brand_analysis.py        # Phase 1
├── desire_mapping.py        # Phase 2
├── competitor_research.py   # Phase 3
├── community_research.py    # Phase 4
├── market_analysis.py       # Phase 5
└── final_report.py          # Phase 6
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
├── settings.py                # Provider config, env checks, paths
├── prompts/                   # Research methodology (gitignored)
├── prompts.example/           # Public templates
├── tools/
│   ├── batch_search.py        # Exa batch search
│   ├── visit_page.py          # Jina Reader + LLM extraction
│   └── save_report.py         # File output
├── input/                     # Example input files
├── output/                    # Generated reports (gitignored)
├── tests/                     # Offline unit tests
├── .github/workflows/ci.yml   # Test workflow
├── .env                       # API keys (gitignored)
├── .env.example               # API key template
├── pyproject.toml             # Dependencies
└── README.md
```

## Development

Run the offline test suite:

```bash
uv sync
uv run python -m unittest discover -s tests -t . -v
```

The tests do not call Exa, Jina, or any LLM. CI runs the same command on Python 3.11.

## LLM provider details

### Ollama Cloud (default, free tier)

```env
LLM_PROVIDER=ollama_cloud
OLLAMA_API_KEY=ok-...
```

- Default model: `gpt-oss:20b-cloud` (free, good for testing)
- Upgrade: set `OLLAMA_MODEL=gpt-oss:120b-cloud`
- Limits: 1 concurrent model, session and weekly caps

### OpenAI (paid)

```env
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-...
```

- Default model: `gpt-4o-mini`
- Override with `OPENAI_MODEL=gpt-4o`
- Better quality, no free-tier session caps, costs money

### Optional overrides

| Variable | Default | Purpose |
|---|---|---|
| `OLLAMA_MODEL` | `gpt-oss:20b-cloud` | Main model on Ollama Cloud |
| `OPENAI_MODEL` | `gpt-4o-mini` | Main model on OpenAI |
| `EXTRACTION_MODEL` | provider default | Model used by `visit_page` |
| `LLM_TEMPERATURE` | `0.7` | Main model temperature |
| `LLM_BASE_URL` | `https://ollama.com/v1` | Ollama-compatible endpoint |
| `OPENAI_BASE_URL` | unset | Optional OpenAI-compatible endpoint |

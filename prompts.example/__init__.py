"""Example prompts for the Market Research Agent.

This is a TEMPLATE directory — not an importable Python package.
The directory name `prompts.example` contains a dot, which Python's
import system treats as a package separator, so it cannot be imported
directly. It is meant to be read, customized, and copied into `prompts/`.

To use these example prompts as a starting point:
1. Copy this directory's contents into the prompts/ directory:
       Copy-Item -Path prompts.example\\*.py -Destination prompts\\ -Force
   (On macOS/Linux: cp prompts.example/*.py prompts/)
2. Edit each file in prompts/ with your own research questions and methodology
3. Run the agent: python market_research_crew.py

The imports below intentionally reference `prompts.X` (not `prompts.example.X`)
so that this file works correctly once it is placed inside prompts/__init__.py.
When this file lives in prompts.example/, it is a reference document only.

Each file (system_prompt.py, brand_analysis.py, etc.) is self-contained and
defines a single prompt constant. See prompts.example/README.md for details.
"""

# NOTE: These imports are written to match prompts/__init__.py exactly.
# They will only resolve at runtime once this file is copied to prompts/__init__.py.
from prompts.system_prompt import SYSTEM_PROMPT
from prompts.brand_analysis import BRAND_ANALYSIS_PROMPT
from prompts.desire_mapping import DESIRE_MAPPING_PROMPT
from prompts.competitor_research import COMPETITOR_RESEARCH_PROMPT
from prompts.community_research import COMMUNITY_RESEARCH_PROMPT
from prompts.market_analysis import MARKET_ANALYSIS_PROMPT
from prompts.final_report import FINAL_REPORT_PROMPT

MARKET_RESEARCH_PROMPT = f"""{SYSTEM_PROMPT}

{BRAND_ANALYSIS_PROMPT}

{DESIRE_MAPPING_PROMPT}

{COMPETITOR_RESEARCH_PROMPT}

{COMMUNITY_RESEARCH_PROMPT}

{MARKET_ANALYSIS_PROMPT}

{FINAL_REPORT_PROMPT}
"""

__all__ = [
    "SYSTEM_PROMPT",
    "BRAND_ANALYSIS_PROMPT",
    "DESIRE_MAPPING_PROMPT",
    "COMPETITOR_RESEARCH_PROMPT",
    "COMMUNITY_RESEARCH_PROMPT",
    "MARKET_ANALYSIS_PROMPT",
    "FINAL_REPORT_PROMPT",
    "MARKET_RESEARCH_PROMPT",
]

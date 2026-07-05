from crewai import Agent, Task, Crew, Process, LLM
from crewai_tools import ScrapeWebsiteTool
from tools.batch_search import BatchSearchTool
from tools.visit_page import VisitPageTool
from tools.save_report import SaveReportTool
from prompts import (
    SYSTEM_PROMPT,
    BRAND_ANALYSIS_PROMPT,
    DESIRE_MAPPING_PROMPT,
    COMPETITOR_RESEARCH_PROMPT,
    COMMUNITY_RESEARCH_PROMPT,
    MARKET_ANALYSIS_PROMPT,
    FINAL_REPORT_PROMPT,
    MARKET_RESEARCH_PROMPT,
)
import os
import re
from dotenv import load_dotenv

load_dotenv()

# ============================================================================
# Tool initialization
# ============================================================================
batch_search = BatchSearchTool()
visit_page = VisitPageTool()
scrape_website = ScrapeWebsiteTool()
save_report = SaveReportTool()

# ============================================================================
# LLM configuration
# ============================================================================
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
else:
    llm = LLM(
        model="openai/gpt-oss:20b-cloud",
        temperature=0.7,
        base_url="https://ollama.com/v1",
        api_key=os.getenv("OLLAMA_API_KEY")
    )
    print("Using Ollama Cloud (gpt-oss:20b-cloud)")

# ============================================================================
# Single Agent - Deep Market Research Analyst
# ============================================================================
market_researcher = Agent(
    role="Deep Market Research Analyst",
    goal=SYSTEM_PROMPT,
    backstory=(
        "You are an elite market researcher with 20+ years of experience in "
        "consumer psychology, competitive analysis, and advertising strategy. "
        "You conduct thorough multi-source investigations, visiting websites, "
        "reading reviews, analyzing Reddit discussions, and studying social media. "
        "You think strategically about positioning, desires, and market sophistication. "
        "You always use your tools to gather real data before making conclusions. "
        "You never fabricate information - if you can't find it, you say so."
    ),
    tools=[batch_search, visit_page, scrape_website, save_report],
    verbose=True,
    allow_delegation=False,
    llm=llm,
    max_iter=25,
    memory=False,
)

# ============================================================================
# Tasks - Broken into phases so the agent uses tools between each phase
# ============================================================================

# Phase 1: Brand analysis (scrape website + search)
brand_analysis_task = Task(
    description=f"""Research the brand at: {{brand_website}}

Additional product info: {{product_info}}

{BRAND_ANALYSIS_PROMPT}

Use scrape_website on {{brand_website}} first, then batch_search for additional context.
Include direct quotes and source links.""",
    expected_output="A detailed brand analysis (2-3 pages) with source links.",
    agent=market_researcher,
)

# Phase 2: Desire + Problem mapping (search + visit pages)
desire_mapping_task = Task(
    description=f"""{DESIRE_MAPPING_PROMPT}

Use batch_search with queries like:
- "why developers use boilerplates"
- "pain points building SaaS from scratch"
- "shipfast alternatives problems"
- "indie hacker struggles launching products"

Then use visit_page on the most relevant results to get detailed content.
Include 5-7 direct quotes per desire with source links.""",
    expected_output="A detailed desire and problem mapping (2-3 pages) with quotes and sources.",
    agent=market_researcher,
)

# Phase 3: Competitor research (search + visit competitor sites)
competitor_research_task = Task(
    description=f"""Research competitors for: {{brand_website}}

{COMPETITOR_RESEARCH_PROMPT}

Use batch_search with queries like:
- "shipfast alternatives"
- "Next.js boilerplate competitors"
- "best SaaS starter kits"
- "indie hacker boilerplate comparison"

Then use visit_page on at least 3-5 competitor websites to analyze them.
Include specific examples and links.""",
    expected_output="A comprehensive competitor analysis (2-3 pages) with links.",
    agent=market_researcher,
)

# Phase 4: Reddit + Amazon research (search + visit threads/reviews)
community_research_task = Task(
    description=f"""{COMMUNITY_RESEARCH_PROMPT}

Use batch_search with queries like:
- "site:reddit.com shipfast"
- "site:reddit.com Next.js boilerplate"
- "site:reddit.com indie hacker SaaS starter"
- "shipfast amazon review"
- "Next.js boilerplate amazon"

Then use visit_page on the most relevant Reddit threads and review pages.
Include direct links to all threads.""",
    expected_output="A rich collection of authentic customer language (2-3 pages) with links.",
    agent=market_researcher,
)

# Phase 5: Social media + market sophistication
market_analysis_task = Task(
    description=f"""{MARKET_ANALYSIS_PROMPT}

Use batch_search with queries like:
- "shipfast tiktok"
- "Next.js boilerplate instagram"
- "SaaS starter kit facebook ads"
- "developer tools advertising trends"

Then visit relevant pages to analyze content.
Include links to specific content.""",
    expected_output="A market analysis covering social media and sophistication (2-3 pages).",
    agent=market_researcher,
)

# Phase 6: Final report compilation (uses save_report tool)
final_report_task = Task(
    description=f"""FINAL STEP: Compile all your research into a comprehensive market research report.

Based on all the research you've conducted in previous tasks, create the final document.

{FINAL_REPORT_PROMPT}

Use the save_report tool to save your report. Pass the full report content and use the brand name from {{brand_website}} as the filename.""",
    expected_output="A comprehensive 25+ page market research document saved to output/ folder.",
    agent=market_researcher,
)

# ============================================================================
# Crew - Single agent, multiple sequential tasks
# ============================================================================
market_research_crew = Crew(
    agents=[market_researcher],
    tasks=[
        brand_analysis_task,
        desire_mapping_task,
        competitor_research_task,
        community_research_task,
        market_analysis_task,
        final_report_task,
    ],
    process=Process.sequential,
    verbose=True,
)


# ============================================================================
# CLI Interface
# ============================================================================
def run_market_research(brand_website: str, product_info: str = ""):
    """Run the comprehensive market research crew."""
    print(f"🚀 Starting market research for: {brand_website}")
    print("=" * 60)

    result = market_research_crew.kickoff(
        inputs={
            "brand_website": brand_website,
            "product_info": product_info
        }
    )

    print("\n" + "=" * 60)
    print("✅ Market research completed!")
    print("\n📋 Final Report Summary:")
    print(result)

    # Also save via Python (backup in case agent didn't use save_report tool)
    output_dir = os.path.join(os.path.dirname(__file__), "output")
    os.makedirs(output_dir, exist_ok=True)

    brand_name = re.sub(
        r'[^a-zA-Z0-9]',
        '_',
        brand_website.replace("https://", "").replace("http://", "").replace("www.", "").split("/")[0]
    )
    output_file = os.path.join(output_dir, f"{brand_name}_market_research.md")

    report_content = f"""# Market Research Report: {brand_website}

## Product Information
{product_info}

---

## Research Findings

{str(result)}

---

*Generated by Single-Agent Deep Market Research System*
"""

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(report_content)

    print(f"\n📄 Report saved to: {output_file}")

    return result


def parse_input_file(filepath: str):
    """Parse an input file to extract brand_website and product_info.

    Expected format:
        website: https://example.com
        product: Some product info here
    """
    brand_website = ""
    product_info = ""

    with open(filepath, "r", encoding="utf-8") as f:
        lines = f.readlines()

    for line in lines:
        line = line.strip()
        if line.lower().startswith("website:"):
            brand_website = line.split(":", 1)[1].strip()
        elif line.lower().startswith("product:"):
            product_info = line.split(":", 1)[1].strip()

    return brand_website, product_info


if __name__ == "__main__":
    import sys
    import os

    input_dir = os.path.join(os.path.dirname(__file__), "input")

    if len(sys.argv) > 1:
        # Run with a specific input file: python market_research_crew.py input/example_saas.txt
        input_file = sys.argv[1]
        if not os.path.isabs(input_file) and not os.path.exists(input_file):
            input_file = os.path.join(input_dir, input_file)
        brand_site, product_details = parse_input_file(input_file)
        print(f"📄 Loaded input from: {input_file}")
    else:
        # Interactive mode
        print("Available example inputs in input/ folder:")
        if os.path.exists(input_dir):
            for f in os.listdir(input_dir):
                if f.endswith(".txt"):
                    print(f"  - input/{f}")
        print()

        brand_site = input("Enter brand website OR input filename (e.g., input/example_saas.txt): ").strip()

        # If input is a file path, load from it
        if brand_site.endswith(".txt") or "/" in brand_site or "\\" in brand_site:
            filepath = brand_site
            if not os.path.isabs(filepath):
                filepath = os.path.join(input_dir, os.path.basename(filepath))
            brand_site, product_details = parse_input_file(filepath)
            print(f"📄 Loaded input from: {filepath}")
        else:
            product_details = input("Enter any additional product information (optional): ").strip()

    if not brand_site:
        print("❌ No brand website provided. Exiting.")
        sys.exit(1)

    run_market_research(brand_site, product_details)

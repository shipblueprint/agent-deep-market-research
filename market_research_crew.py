"""Single-agent market research CLI built with CrewAI."""

import importlib
import os
import sys

from crewai import Agent, Crew, LLM, Process, Task
from crewai_tools import ScrapeWebsiteTool
from dotenv import load_dotenv

import settings
from tools.batch_search import BatchSearchTool
from tools.visit_page import VisitPageTool
from tools.save_report import SaveReportTool

load_dotenv()


def load_prompts():
    """Import prompts/, creating it from prompts.example/ on first run."""
    settings.ensure_prompts()
    return importlib.import_module("prompts")


def build_crew(llm: LLM) -> Crew:
    """Build the single-agent, six-phase research crew."""
    prompts = load_prompts()

    batch_search = BatchSearchTool()
    visit_page = VisitPageTool()
    scrape_website = ScrapeWebsiteTool()
    save_report = SaveReportTool()

    market_researcher = Agent(
        role="Deep Market Research Analyst",
        goal=prompts.SYSTEM_PROMPT,
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

    brand_analysis_task = Task(
        description=f"""Research the brand at: {{brand_website}}

Additional product info: {{product_info}}

{prompts.BRAND_ANALYSIS_PROMPT}

Use scrape_website on {{brand_website}} first, then batch_search for additional context.
Include direct quotes and source links.""",
        expected_output="A detailed brand analysis (2-3 pages) with source links.",
        agent=market_researcher,
    )

    desire_mapping_task = Task(
        description=f"""{prompts.DESIRE_MAPPING_PROMPT}

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

    competitor_research_task = Task(
        description=f"""Research competitors for: {{brand_website}}

{prompts.COMPETITOR_RESEARCH_PROMPT}

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

    community_research_task = Task(
        description=f"""{prompts.COMMUNITY_RESEARCH_PROMPT}

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

    market_analysis_task = Task(
        description=f"""{prompts.MARKET_ANALYSIS_PROMPT}

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

    final_report_task = Task(
        description=f"""FINAL STEP: Compile all your research into a comprehensive market research report.

Based on all the research you've conducted in previous tasks, create the final document.

{prompts.FINAL_REPORT_PROMPT}

Use the save_report tool to save your report. Pass the full report content and use the brand name from {{brand_website}} as the filename.""",
        expected_output="A comprehensive market research document saved to the output/ folder.",
        agent=market_researcher,
    )

    return Crew(
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


def run_market_research(brand_website: str, product_info: str = ""):
    """Run the comprehensive market research crew."""
    settings.validate_environment()
    print(f"🚀 Starting market research for: {brand_website}")
    print("=" * 60)

    llm = LLM(**settings.llm_kwargs())
    print(f"Using {settings.provider_label()}")

    crew = build_crew(llm)
    result = crew.kickoff(
        inputs={
            "brand_website": brand_website,
            "product_info": product_info,
        }
    )

    print("\n" + "=" * 60)
    print("✅ Market research completed!")
    print("\n📋 Final Report Summary:")
    print(result)

    reports = []
    if settings.OUTPUT_DIR.is_dir():
        reports = sorted(
            settings.OUTPUT_DIR.glob("*_market_research.md"),
            key=lambda path: path.stat().st_mtime,
        )
    if reports:
        print(f"\n📄 Report saved to: {reports[-1]}")
    else:
        print("\n⚠️ No report file found in output/. The agent did not call save_report.")

    return result


def parse_input_file(filepath: str):
    """Parse an input file to extract brand_website and product_info.

    Expected format:
        website: https://example.com
        product: Some product info here
    """
    if not os.path.isfile(filepath):
        raise SystemExit(f"Input file not found: {filepath}")

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


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    input_dir = os.path.join(os.path.dirname(__file__), "input")

    if argv and argv[0] in {"--check", "-c"}:
        settings.ensure_prompts()
        settings.validate_environment()
        print("Environment OK: required keys are present.")
        return 0

    if argv and argv[0] in {"--help", "-h"}:
        print("Usage: uv run python market_research_crew.py [input-file] [--check]")
        return 0

    if argv:
        # Run with a specific input file: uv run python market_research_crew.py input/example_saas.txt
        input_file = argv[0]
        if not os.path.isabs(input_file) and not os.path.exists(input_file):
            input_file = os.path.join(input_dir, input_file)
        brand_site, product_details = parse_input_file(input_file)
        print(f"📄 Loaded input from: {input_file}")
    else:
        # Interactive mode
        print("Available example inputs in input/ folder:")
        if os.path.exists(input_dir):
            for filename in sorted(os.listdir(input_dir)):
                if filename.endswith(".txt"):
                    print(f"  - input/{filename}")
        print()

        brand_site = input(
            "Enter brand website OR input filename (e.g., input/example_saas.txt): "
        ).strip()

        # If input is a file path, load from it
        if brand_site.endswith(".txt") or "/" in brand_site or "\\" in brand_site:
            filepath = brand_site
            if not os.path.isabs(filepath):
                filepath = os.path.join(input_dir, os.path.basename(filepath))
            brand_site, product_details = parse_input_file(filepath)
            print(f"📄 Loaded input from: {filepath}")
        else:
            product_details = input(
                "Enter any additional product information (optional): "
            ).strip()

    if not brand_site:
        print("❌ No brand website provided. Exiting.")
        return 1

    run_market_research(brand_site, product_details)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

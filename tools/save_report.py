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

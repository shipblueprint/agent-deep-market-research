from crewai.tools import BaseTool

import settings


class SaveReportTool(BaseTool):
    name: str = "save_report"
    description: str = (
        "Save the market research report to a markdown file. "
        "Pass the full report content and a brand name for the filename. "
        "The file will be saved in the output/ folder."
    )

    def _run(self, content: str, brand_name: str = "report") -> str:
        settings.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        filepath = settings.report_path(brand_name)
        filepath.write_text(content, encoding="utf-8")
        return f"Report saved to: {filepath}"

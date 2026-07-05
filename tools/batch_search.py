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

    def _run(self, queries) -> str:
        if isinstance(queries, str):
            queries = [queries]

        exa = Exa(api_key=os.getenv("EXA_API_KEY"))
        results = []

        for query in queries:
            try:
                response = exa.search_and_contents(
                    query,
                    num_results=5,
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

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
1. Locate the specific sections/data directly related to the user's goal within the webpage content
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
    except Exception:
        return text[:max_tokens * 4]


class VisitPageTool(BaseTool):
    name: str = "visit_page"
    description: str = (
        "Visit webpage(s) and get a summary of relevant content. "
        "Pass a URL (or list of URLs) and a research goal describing what you want to learn. "
        "Returns extracted evidence and a summary - not the raw full page."
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

            try:
                raw = raw.replace("```json", "").replace("```", "").strip()
                parsed = json.loads(raw)
                evidence = parsed.get("evidence", raw)
                summary = parsed.get("summary", "")
            except Exception:
                evidence = raw
                summary = ""

            return f"URL: {url}\nEvidence: {evidence}\nSummary: {summary}\n"
        except Exception as e:
            return f"URL: {url}\nContent (truncated): {content[:2000]}\n[Extraction failed: {str(e)}]\n"

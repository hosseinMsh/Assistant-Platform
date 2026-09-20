import os
from pathlib import Path
from app.core.config import config

TOOL_SCHEMA = {
    "name": "university_knowledge_lookup",
    "description": "Search Sharif University of Technology knowledge base by domain, keyword, or faculty.",
    "requires_confirmation": False,
    "parameters": {
        "type": "object",
        "properties": {
            "domain": {"type": "string"},
            "keyword": {"type": "string"},
            "faculty": {"type": "string"}
        }
    }
}

def execute(domain: str = "", keyword: str = "", faculty: str = "") -> dict:
    knowledge_path = Path(config.knowledge_path)
    matches = []
    if knowledge_path.exists():
        for file_path in knowledge_path.rglob("*.md"):
            try:
                content = file_path.read_text(encoding="utf-8")
                text = content.lower()
                if domain and domain.lower() not in str(file_path).lower() and domain.lower() not in text:
                    continue
                if keyword and keyword.lower() not in text:
                    continue
                if faculty and faculty.lower() not in str(file_path).lower() and faculty.lower() not in text:
                    continue
                matches.append(str(file_path.relative_to(knowledge_path)))
            except Exception:
                continue
    return {
        "found": len(matches) > 0,
        "domain": domain,
        "keyword": keyword,
        "faculty": faculty,
        "matches": matches[:20],
        "count": len(matches),
        "message": f"Found {len(matches)} knowledge entries." if matches else "No matching entries found."
    }

import httpx

class KnowledgeClient:
    def __init__(self, base_url: str = "http://localhost:8080"):
        self.client = httpx.Client(base_url=base_url, timeout=10.0)

    def lookup(self, domain: str = "", keyword: str = "") -> dict:
        resp = self.client.get("/v1/tools", params={"domain": domain, "keyword": keyword})
        resp.raise_for_status()
        return resp.json()

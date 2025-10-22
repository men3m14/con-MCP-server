# ==============================================================
# 🧠 Confluence MCP Server
# --------------------------------------------------------------
# Exposes your Confluence space to AI agents using the
# Model Context Protocol (MCP).
#
# Features:
#   • Resource: Fetch a Confluence page by ID
#   • Tool: Search pages by keyword
#
# Requirements:
#   pip install requests python-dotenv model-context-protocol
# ==============================================================

import os
import requests
from dotenv import load_dotenv

# Attempt to import the real MCP SDK; fallback to a simple mock
try:
    from mcp.server import Server
    from mcp.types import ResourceContent
except ImportError:
    print("⚠️ MCP SDK not found — using mock mode for testing.\n")

    class ResourceContent:
        def __init__(self, uri, mime_type, data):
            self.uri = uri
            self.mime_type = mime_type
            self.data = data

    class Server:
        def __init__(self, name):
            self.name = name
            print(f"[MOCK MCP] Server '{name}' initialized")

        def resource(self, name):
            def decorator(func):
                print(f"[MOCK MCP] Resource '{name}' registered")
                return func
            return decorator

        def tool(self, name):
            def decorator(func):
                print(f"[MOCK MCP] Tool '{name}' registered")
                return func
            return decorator

        def run_stdio(self):
            print(f"[MOCK MCP] '{self.name}' server running (simulation)")
            while True:
                cmd = input("Enter 'search <keyword>' or 'page <id>': ").strip()
                if cmd.startswith("search "):
                    kw = cmd.split(" ", 1)[1]
                    print(search_confluence(kw))
                elif cmd.startswith("page "):
                    pid = cmd.split(" ", 1)[1]
                    print(get_page_content(pid))
                elif cmd.lower() in ["exit", "quit"]:
                    break

# --------------------------------------------------------------
# 1️⃣ Load configuration
# --------------------------------------------------------------
load_dotenv()
CONFLUENCE_BASE_URL = os.getenv("CONFLUENCE_BASE_URL")
ATLASSIAN_EMAIL = os.getenv("ATLASSIAN_EMAIL")
ATLASSIAN_TOKEN = os.getenv("ATLASSIAN_TOKEN")

# --------------------------------------------------------------
# 2️⃣ Initialize MCP server
# --------------------------------------------------------------
app = Server("confluence")

# --------------------------------------------------------------
# 3️⃣ Helper: Fetch page content
# --------------------------------------------------------------
def get_page_content(page_id: str) -> str:
    url = f"{CONFLUENCE_BASE_URL}/content/{page_id}?expand=body.storage"
    resp = requests.get(url, auth=(ATLASSIAN_EMAIL, ATLASSIAN_TOKEN))

    if resp.status_code != 200:
        raise Exception(f"Failed to fetch page {page_id}: {resp.status_code} - {resp.text}")

    data = resp.json()
    return data["body"]["storage"]["value"]

# --------------------------------------------------------------
# 4️⃣ Resource: Get a page
# --------------------------------------------------------------
@app.resource("confluence.page")
def get_page_resource(page_id: str):
    html_content = get_page_content(page_id)
    return ResourceContent(
        uri=f"confluence://page/{page_id}",
        mime_type="text/html",
        data=html_content
    )

# --------------------------------------------------------------
# 5️⃣ Tool: Search Confluence
# --------------------------------------------------------------
@app.tool("search_confluence")
def search_confluence(query: str):
    url = f"{CONFLUENCE_BASE_URL}/content/search?cql=text~\"{query}\""
    resp = requests.get(url, auth=(ATLASSIAN_EMAIL, ATLASSIAN_TOKEN))
    resp.raise_for_status()

    results = resp.json().get("results", [])
    output = []
    for r in results:
        title = r["title"]
        page_id = r["id"]
        link = f"https://muhammed-abdelmoniem.atlassian.net/wiki{r['_links']['webui']}"
        output.append({"title": title, "id": page_id, "url": link})

    return output

# --------------------------------------------------------------
# 6️⃣ Run server (or mock shell)
# --------------------------------------------------------------
if __name__ == "__main__":
    print("🚀 Starting Confluence MCP Server...")
    app.run_stdio()


import json, os, sys
from pathlib import Path
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from openai import OpenAI
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

BASE_DIR = Path(__file__).parent
load_dotenv(BASE_DIR / ".env")
ENDPOINT = os.getenv("FOUNDRY_ENDPOINT", "").rstrip("/")
API_KEY = os.getenv("FOUNDRY_API_KEY", "")
MODEL = os.getenv("FOUNDRY_MODEL", "")
INVENTORY_FILE = BASE_DIR / "data" / "cloud_inventory.json"

app = FastAPI(title="CloudOps MCP Studio", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=False, allow_methods=["*"], allow_headers=["*"])
SYSTEM_PROMPT = """You are CloudOps Copilot. Use MCP tools for inventory and status questions. This is a SIMULATED demo inventory only; no live Azure resources were queried. Never claim to change, start, stop, create or remediate infrastructure. Explain findings simply and recommend safe diagnostic next steps."""

class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)

def load_inventory():
    with INVENTORY_FILE.open("r", encoding="utf-8") as f:
        return json.load(f)

def convert_tools(items):
    return [{"type":"function","function":{"name":t.name,"description":t.description or "", "parameters":t.inputSchema}} for t in items]

def result_text(result):
    if getattr(result, "structuredContent", None) is not None:
        return json.dumps(result.structuredContent, ensure_ascii=False)
    return "\\n".join(x.text for x in result.content if hasattr(x, "text")) or "{}"

async def run_agent(message):
    if not ENDPOINT or not API_KEY or not MODEL:
        raise HTTPException(status_code=503, detail="Foundry not configured. Copy backend/.env.example to backend/.env and fill in endpoint, key and deployment name.")
    llm = OpenAI(api_key=API_KEY, base_url=f"{ENDPOINT}/openai/v1/")
    params = StdioServerParameters(command=sys.executable, args=[str(BASE_DIR/"mcp_server.py")])
    events = []
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            found = await session.list_tools()
            tools = convert_tools(found.tools)
            messages = [{"role":"system","content":SYSTEM_PROMPT},{"role":"user","content":message}]
            for _ in range(5):
                try:
                    response = llm.chat.completions.create(model=MODEL, messages=messages, tools=tools, tool_choice="auto", max_completion_tokens=1200)
                except Exception as exc:
                    raise HTTPException(status_code=502, detail=f"Foundry request failed: {exc}")
                assistant = response.choices[0].message
                if not assistant.tool_calls:
                    return {"answer":assistant.content or "No response returned.", "tool_events":events, "model":MODEL, "simulated":True}
                messages.append(assistant.model_dump(exclude_none=True))
                for call in assistant.tool_calls:
                    try: args = json.loads(call.function.arguments or "{}")
                    except json.JSONDecodeError: args = {}
                    event = {"tool":call.function.name, "arguments":args}
                    try:
                        result = await session.call_tool(call.function.name, arguments=args)
                        text = result_text(result)
                        event["result"] = json.loads(text)
                        event["success"] = not getattr(result, "isError", False)
                    except Exception as exc:
                        text = json.dumps({"error":str(exc)})
                        event["result"] = {"error":str(exc)}
                        event["success"] = False
                    events.append(event)
                    messages.append({"role":"tool","tool_call_id":call.id,"content":text})
    raise HTTPException(status_code=502, detail="The model reached the tool-call limit.")

@app.get("/api/health")
def health():
    return {"status":"online","service":"CloudOps MCP Studio","foundry_configured":bool(ENDPOINT and API_KEY and MODEL),"model":MODEL or "Not configured","inventory_is_simulated":True}

@app.get("/api/resources")
def resources():
    data = load_inventory()
    return {"inventory_name":data["inventory_name"],"is_simulated":data["is_simulated"],"last_updated":data["last_updated"],"resources":data["resources"]}

@app.post("/api/chat")
async def chat(request: ChatRequest):
    return await run_agent(request.message)

FRONTEND_DIR = BASE_DIR.parent / "frontend"
app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")

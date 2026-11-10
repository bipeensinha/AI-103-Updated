"""Console demo: Foundry GPT-5 -> Python MCP client -> local SQL MCP server."""
import asyncio, json, os, sys
from pathlib import Path
from dotenv import load_dotenv
from openai import AzureOpenAI
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")

client = AzureOpenAI(
    azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
    api_key=os.environ["AZURE_OPENAI_API_KEY"],
    api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2025-04-01-preview"),
)
MODEL = os.environ["AZURE_OPENAI_DEPLOYMENT"]
SERVER = ROOT / "mcp_sql" / "server.py"

TOOLS = [
    {"type":"function","name":"test_sql_connection",
     "description":"Test the configured SQL Server connection.",
     "parameters":{"type":"object","properties":{},"required":[],"additionalProperties":False},
     "strict":True},
    {"type":"function","name":"list_tables",
     "description":"List database tables in a schema, normally dbo.",
     "parameters":{"type":"object","properties":{"schema_name":{"type":"string"}},
                  "required":["schema_name"],"additionalProperties":False},"strict":True},
    {"type":"function","name":"describe_table",
     "description":"Inspect columns and types of a known table before querying it.",
     "parameters":{"type":"object","properties":{"table_name":{"type":"string"},
                  "schema_name":{"type":"string"}},
                  "required":["table_name","schema_name"],"additionalProperties":False},"strict":True},
    {"type":"function","name":"run_readonly_query",
     "description":"Run one SELECT query only. Use only known tables/columns. Maximum 100 rows.",
     "parameters":{"type":"object","properties":{"sql":{"type":"string"},
                  "max_rows":{"type":"integer"}},
                  "required":["sql","max_rows"],"additionalProperties":False},"strict":True},
]

async def invoke_mcp(session, tool_name, arguments):
    result = await session.call_tool(tool_name, arguments)
    if result.isError:
        raise RuntimeError(str(result.content))
    # Our MCP tools return JSON-serializable dicts as text content.
    texts = [block.text for block in result.content if getattr(block, "text", None)]
    joined = "\n".join(texts)
    try:
        return json.loads(joined)
    except json.JSONDecodeError:
        return {"result": joined}

async def ask(question):
    params = StdioServerParameters(
        command=sys.executable,
        args=[str(SERVER)],
        env=os.environ.copy(),
    )
    async with stdio_client(params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            response = client.responses.create(
                model=MODEL,
                instructions=(
                    "You are a SQL data assistant. Use MCP tools to inspect the database "
                    "and answer accurately. Never invent records. Inspect tables and columns "
                    "before querying unfamiliar data. Use read-only SELECT queries only. "
                    "Do not retrieve unnecessary personal or sensitive data."
                ),
                input=question,
                tools=TOOLS,
            )
            while True:
                calls = [x for x in response.output
                         if getattr(x, "type", None) == "function_call"]
                if not calls:
                    print("\nGPT-5:", response.output_text)
                    return
                outputs = []
                for call in calls:
                    args = json.loads(call.arguments or "{}")
                    print(f"\n[MCP tool call] {call.name} {args}")
                    try:
                        result = await invoke_mcp(session, call.name, args)
                        output = json.dumps(result, default=str)
                    except Exception as exc:
                        output = json.dumps({"error": str(exc)})
                    outputs.append({"type":"function_call_output",
                                    "call_id":call.call_id,"output":output})
                response = client.responses.create(
                    model=MODEL,
                    previous_response_id=response.id,
                    input=outputs,
                    tools=TOOLS,
                )

async def main():
    print("SQL Server + MCP + Foundry GPT-5 demo. Type exit to quit.")
    while True:
        question = input("\nYou: ").strip()
        if question.lower() in ("exit", "quit"):
            break
        if question:
            try:
                await ask(question)
            except Exception as e:
                print(f"\nError: {e}")

if __name__ == "__main__":
    asyncio.run(main())

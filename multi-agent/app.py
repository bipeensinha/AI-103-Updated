from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from Corporate_user_helpdesk import solve_problem, AZURE_OPENAI_DEPLOYMENT


# ============================================================
# CREATE FASTAPI APPLICATION
# ============================================================

app = FastAPI(
    title="Enterprise AI Service Desk",
    description="Multi-Agent IT Helpdesk powered by Microsoft Foundry GPT-5",
    version="2.0"
)


# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"]
)


# ============================================================
# REQUEST MODEL
# ============================================================

class ProblemRequest(BaseModel):
    problem: str


# ============================================================
# MAIN MULTI-AGENT API
# ============================================================

@app.post("/api/solve")
def solve_problem_api(request: ProblemRequest):

    problem = request.problem.strip()

    if not problem:
        return {
            "employee_request": "",
            "selected_agents": [],
            "findings": {},
            "memory": {},
            "final_answer": "Please enter an IT problem."
        }

    return solve_problem(problem)


# ============================================================
# HEALTH CHECK
# ============================================================

@app.get("/api/health")
def health():

    return {
        "status": "online",
        "service": "Enterprise AI Service Desk",
        "platform": "Microsoft Foundry",
        "model": AZURE_OPENAI_DEPLOYMENT,
        "agents": [
            "Orchestrator",
            "Identity",
            "Network",
            "Endpoint",
            "Resolution"
        ]
    }


# ============================================================
# SERVE FRONTEND
# ============================================================

app.mount(
    "/",
    StaticFiles(
        directory="static",
        html=True
    ),
    name="static"
)

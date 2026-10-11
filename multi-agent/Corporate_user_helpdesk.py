# ============================================================
# ENTERPRISE AI SERVICE DESK
# MULTI-AGENT SYSTEM - MICROSOFT FOUNDRY GPT-5
# ============================================================
#
# Demonstrates:
# 1. AI Agent
# 2. Orchestrator Agent
# 3. Multiple Specialist Agents
# 4. Context Passing
# 5. Short-Term Memory
# 6. Resolution Agent
#
# Azure / Microsoft Foundry:
# - Uses the OpenAI Python SDK
# - Uses the Azure OpenAI /openai/v1 Responses API
# - AZURE_OPENAI_DEPLOYMENT must be the deployment name
#
# Can be used by:
# 1. FastAPI Web UI
# 2. Standalone Terminal Demo
# ============================================================

import json
import os
import re

from openai import OpenAI


# ============================================================
# 1. CONFIGURATION
# ============================================================

AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT", "").strip()
AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY", "").strip()
AZURE_OPENAI_DEPLOYMENT = os.getenv(
    "AZURE_OPENAI_DEPLOYMENT",
    "gpt-5"
).strip()

if not AZURE_OPENAI_ENDPOINT:
    raise RuntimeError(
        "AZURE_OPENAI_ENDPOINT is not set. "
        "Add it to your .env file before starting the application."
    )

if not AZURE_OPENAI_API_KEY:
    raise RuntimeError(
        "AZURE_OPENAI_API_KEY is not set. "
        "Add your Azure OpenAI / Microsoft Foundry API key to .env."
    )

client = OpenAI(
    api_key=AZURE_OPENAI_API_KEY,
    base_url=f"{AZURE_OPENAI_ENDPOINT.rstrip('/')}/openai/v1/"
)


# ============================================================
# 2. SHORT-TERM MEMORY
# ============================================================

short_term_memory = {
    "employee_request": "",
    "orchestrator_decision": [],
    "agent_findings": []
}


# ============================================================
# 3. GENERIC GPT-5 FUNCTION
# ============================================================

def call_ai(system_message, user_message, max_output_tokens=1200):
    """
    Call Microsoft Foundry / Azure OpenAI using the Responses API.

    GPT-5 reasoning can consume part of the output budget. Therefore
    this function deliberately uses a reasonable output budget instead
    of the very small local-model limit used in the old Qwen version.
    """

    try:
        response = client.responses.create(
            model=AZURE_OPENAI_DEPLOYMENT,
            instructions=system_message,
            input=user_message,
            max_output_tokens=max_output_tokens
        )

        answer = (response.output_text or "").strip()

        # Important guard:
        # Never silently return an empty specialist result.
        if not answer:
            return "No text was returned by the AI agent."

        return answer

    except Exception as exc:
        print(f"\nAI call failed: {exc}")
        return f"AI agent call failed: {exc}"


# ============================================================
# 4. ORCHESTRATOR AGENT
# ============================================================

def orchestrator(employee_request):
    """
    Decide which specialist agents should investigate the incident.
    The orchestrator does NOT solve the problem.
    """

    prompt = f"""
You are an Enterprise IT Orchestrator Agent.

Employee request:
{employee_request}

Available specialist agents:

IDENTITY
- Account
- Password
- MFA
- User authentication
- Access
- Permissions

NETWORK
- VPN
- Wi-Fi
- Internet
- DNS
- Firewall
- Network connectivity

ENDPOINT
- Laptop
- Desktop
- Device
- VPN client
- Certificate
- Software
- Local configuration

Choose every specialist that is genuinely relevant.

Return ONLY a comma-separated list using these exact names:
IDENTITY
NETWORK
ENDPOINT

Examples:
IDENTITY, NETWORK
ENDPOINT
NETWORK, ENDPOINT

Do not explain your answer.
"""

    decision = call_ai(
        "You are an enterprise IT Orchestrator. "
        "Your only job is to select relevant specialist agents.",
        prompt,
        max_output_tokens=800
    ).upper()

    selected_agents = []

    # Parse only known agent names.
    for agent in ("IDENTITY", "NETWORK", "ENDPOINT"):
        if re.search(rf"\b{agent}\b", decision):
            selected_agents.append(agent)

    # Safety fallback.
    if not selected_agents:
        selected_agents.append("ENDPOINT")

    return selected_agents


# ============================================================
# 5. IDENTITY AGENT
# ============================================================

def identity_agent(context):

    prompt = f"""
Incident context:
{context}

You are the Identity Specialist Agent.

Investigate only identity and access aspects.

Consider:
- Account status
- Password
- MFA
- User access
- Permissions

Return a concise finding in this format:

Finding:
<your finding>

Recommended check:
<one practical check>

Do not invent facts that are not present in the incident.
Do not claim that an account is locked, disabled, or reset unless
the incident provides evidence for it.
"""

    return call_ai(
        "You are an Enterprise Identity Specialist.",
        prompt,
        max_output_tokens=1200
    )


# ============================================================
# 6. NETWORK AGENT
# ============================================================

def network_agent(context):

    prompt = f"""
Incident context:
{context}

You are the Network Specialist Agent.

Investigate only network-related aspects.

Consider:
- VPN
- Wi-Fi
- Internet
- DNS
- Firewall
- Network availability

Return a concise finding in this format:

Finding:
<your finding>

Recommended check:
<one practical check>

Do not invent facts that are not present in the incident.
"""

    return call_ai(
        "You are an Enterprise Network Specialist.",
        prompt,
        max_output_tokens=1200
    )


# ============================================================
# 7. ENDPOINT AGENT
# ============================================================

def endpoint_agent(context):

    prompt = f"""
Incident context:
{context}

You are the Endpoint Specialist Agent.

Investigate only device-side aspects.

Consider:
- Laptop
- VPN client
- Software
- Device configuration
- Certificate
- Local firewall

Return a concise finding in this format:

Finding:
<your finding>

Recommended check:
<one practical check>

Do not invent facts that are not present in the incident.
"""

    return call_ai(
        "You are an Enterprise Endpoint Specialist.",
        prompt,
        max_output_tokens=1200
    )


# ============================================================
# 8. RESOLUTION AGENT
# ============================================================

def resolution_agent(memory):

    findings = memory.get("agent_findings", [])

    # Explicitly expose findings to the resolution model.
    # This prevents the model from having to infer where they are.
    findings_text = "\n\n".join(
        f"{item['agent']} SPECIALIST FINDING:\n{item['finding']}"
        for item in findings
    )

    prompt = f"""
You are the Enterprise IT Resolution Agent.

Employee request:
{memory.get("employee_request", "")}

Orchestrator selected:
{", ".join(memory.get("orchestrator_decision", []))}

SPECIALIST INVESTIGATION RESULTS:
{findings_text if findings_text else "No specialist findings were returned."}

Use the specialist investigation results above.

Provide a short employee-friendly response with exactly these sections:

1. Most likely root cause
2. What to check
3. Recommended next step

Important:
- Do not invent specific facts.
- Clearly distinguish a likely cause from a confirmed cause.
- If the evidence is insufficient, say that it is not yet confirmed.
- Do not say "No findings have been provided yet" when specialist findings
  are present above.
"""

    answer = call_ai(
        "You are an Enterprise IT Resolution Specialist. "
        "Synthesize specialist findings into a practical resolution.",
        prompt,
        max_output_tokens=1800
    )

    # Last-resort deterministic fallback if the model call fails/returns empty.
    if not answer or answer.startswith("AI agent call failed"):
        if findings:
            return (
                "1. Most likely root cause\n"
                "The issue requires review of the specialist findings below.\n\n"
                "2. What to check\n"
                + "\n".join(
                    f"- {item['agent']}: {item['finding']}"
                    for item in findings
                )
                + "\n\n"
                "3. Recommended next step\n"
                "Use the specialist checks above to confirm the cause."
            )

        return (
            "1. Most likely root cause\n"
            "The root cause could not be determined from the available evidence.\n\n"
            "2. What to check\n"
            "Review the affected account, network connection, and endpoint.\n\n"
            "3. Recommended next step\n"
            "Collect the relevant error message and retry the investigation."
        )

    return answer


# ============================================================
# 9. COMPLETE MULTI-AGENT WORKFLOW
# ============================================================

def solve_problem(employee_request):

    employee_request = employee_request.strip()

    if not employee_request:
        return {
            "employee_request": "",
            "selected_agents": [],
            "findings": {},
            "memory": {},
            "final_answer": "Please enter an IT problem."
        }

    # Reset short-term memory for this incident.
    memory = {
        "employee_request": employee_request,
        "orchestrator_decision": [],
        "agent_findings": []
    }

    # --------------------------------------------------------
    # ORCHESTRATOR
    # --------------------------------------------------------

    selected_agents = orchestrator(employee_request)

    memory["orchestrator_decision"] = selected_agents

    # --------------------------------------------------------
    # SHARED CONTEXT
    # --------------------------------------------------------

    context = f"""
Employee Request:
{employee_request}

Orchestrator Decision:
{selected_agents}
"""

    # --------------------------------------------------------
    # SPECIALIST AGENTS
    # --------------------------------------------------------

    findings = {}

    if "IDENTITY" in selected_agents:
        findings["IDENTITY"] = identity_agent(context)

    if "NETWORK" in selected_agents:
        findings["NETWORK"] = network_agent(context)

    if "ENDPOINT" in selected_agents:
        findings["ENDPOINT"] = endpoint_agent(context)

    # --------------------------------------------------------
    # STORE FINDINGS IN SHORT-TERM MEMORY
    # --------------------------------------------------------

    for agent, finding in findings.items():
        memory["agent_findings"].append({
            "agent": agent,
            "finding": finding
        })

    # Keep module-level memory available for teaching/demo purposes.
    short_term_memory.clear()
    short_term_memory.update(memory)

    # --------------------------------------------------------
    # RESOLUTION AGENT
    # --------------------------------------------------------

    final_answer = resolution_agent(memory)

    # --------------------------------------------------------
    # RETURN COMPLETE RESULT
    # --------------------------------------------------------

    return {
        "employee_request": employee_request,
        "selected_agents": selected_agents,
        "findings": findings,
        "memory": memory,
        "final_answer": final_answer
    }


# ============================================================
# 10. TERMINAL DEMO
# ============================================================

if __name__ == "__main__":

    print("\n")
    print("=" * 60)
    print("          ENTERPRISE AI SERVICE DESK")
    print("             MULTI-AGENT DEMO")
    print("=" * 60)

    print("\nMicrosoft Foundry GPT-5 deployment:")
    print(f"  {AZURE_OPENAI_DEPLOYMENT}")

    print("\nEnter the employee IT problem.")
    print("Type END when finished.\n")

    lines = []

    while True:
        line = input()

        if line.strip().upper() == "END":
            break

        lines.append(line)

    employee_request = "\n".join(lines).strip()

    result = solve_problem(employee_request)

    print("\n")
    print("-" * 60)
    print("SHORT-TERM MEMORY")
    print("-" * 60)

    print("\nEmployee Request:")
    print(result["memory"].get("employee_request", ""))

    print("\nOrchestrator Decision:")
    print(result["memory"].get("orchestrator_decision", []))

    print("\nSpecialist Findings:")

    for finding in result["memory"].get("agent_findings", []):
        print(f"\n[{finding['agent']}]")
        print(finding["finding"])

    print("\n")
    print("=" * 60)
    print("              RESOLUTION AGENT")
    print("=" * 60)
    print("\n")
    print(result["final_answer"])
    print("\n")
    print("=" * 60)
    print("                DEMO COMPLETE")
    print("=" * 60)

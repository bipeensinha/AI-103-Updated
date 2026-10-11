/* =========================================================
   ENTERPRISE AI SERVICE DESK
   Frontend Controller
   ========================================================= */


/* ---------------------------------------------------------
   SUBMIT PROBLEM
--------------------------------------------------------- */

async function submitProblem() {

    const problem =
        document.getElementById("problem").value.trim();

    if (!problem) {
        alert("Please describe the IT problem.");
        return;
    }

    resetAgents();

    document.getElementById(
        "memory-request"
    ).innerText = problem;

    addActivity(
        "👤",
        "Employee",
        "Submitted IT request"
    );

    // IMPORTANT:
    // The HTML id is exactly "orchestrator".
    // Do not append "-agent" here.
    setAgent(
        "orchestrator",
        "running",
        "Analyzing request..."
    );

    addActivity(
        "🤖",
        "Orchestrator Agent",
        "Analyzing the issue..."
    );

    try {

        const response = await fetch(
            "/api/solve",
            {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    problem: problem
                })
            }
        );

        if (!response.ok) {
            throw new Error(
                "Backend request failed: " + response.status
            );
        }

        const data = await response.json();

        // -------------------------
        // ORCHESTRATOR
        // -------------------------

        setAgent(
            "orchestrator",
            "completed",
            "Decision completed"
        );

        document.getElementById(
            "memory-decision"
        ).innerText =
            data.selected_agents.join(", ");

        addActivity(
            "🤖",
            "Orchestrator Agent",
            "Selected: " +
            data.selected_agents.join(", ")
        );

        // -------------------------
        // SPECIALISTS
        // -------------------------

        for (const agentName of data.selected_agents) {

            // FIX:
            // setAgent() already expects the BASE id
            // and appends "-agent" internally.
            //
            // Therefore pass "identity", not "identity-agent".
            const agentId =
                agentName.toLowerCase();

            setAgent(
                agentId,
                "running",
                "Investigating..."
            );

            addActivity(
                getAgentIcon(agentName),
                agentName + " Agent",
                "Investigation started..."
            );

            await sleep(800);

            const finding =
                data.findings[agentName] ||
                "No finding was returned by this specialist.";

            setAgent(
                agentId,
                "completed",
                finding
            );

            addActivity(
                "✅",
                agentName + " Agent",
                "Investigation completed"
            );
        }

        // -------------------------
        // MEMORY
        // -------------------------

        document.getElementById(
            "memory-findings"
        ).innerText =
            Object.keys(data.findings || {}).length +
            " specialist finding(s) collected";

        // -------------------------
        // RESOLUTION
        // -------------------------

        setAgent(
            "resolution",
            "running",
            "Analyzing all findings..."
        );

        addActivity(
            "🎯",
            "Resolution Agent",
            "Creating final resolution..."
        );

        await sleep(800);

        setAgent(
            "resolution",
            "completed",
            "Resolution generated"
        );

        document.getElementById(
            "final-answer"
        ).innerText =
            data.final_answer ||
            "No final resolution was returned.";

        addActivity(
            "✅",
            "Resolution Agent",
            "Final resolution completed"
        );

    }

    catch (error) {

        console.error(error);

        setAgent(
            "orchestrator",
            "completed",
            "Backend error"
        );

        document.getElementById(
            "final-answer"
        ).innerText =
            "Unable to connect to the AI backend. " +
            "Check the FastAPI terminal for the error.";

        addActivity(
            "❌",
            "System",
            error.message
        );
    }
}


/* ---------------------------------------------------------
   AGENT STATUS
--------------------------------------------------------- */

function setAgent(
    agent,
    status,
    text
) {

    // HTML specialist IDs:
    // identity-agent
    // network-agent
    // endpoint-agent
    //
    // HTML orchestrator ID:
    // orchestrator
    //
    // HTML resolution ID:
    // resolution-agent
    //
    // Therefore handle orchestrator separately.

    const elementId =
        agent === "orchestrator"
            ? "orchestrator"
            : agent + "-agent";

    const statusId =
        agent === "orchestrator"
            ? "orchestrator-status"
            : agent + "-status";

    const textId =
        agent === "orchestrator"
            ? "orchestrator-text"
            : agent + "-text";

    const element =
        document.getElementById(elementId);

    if (!element) {
        console.warn(
            "Agent element not found:",
            elementId
        );
        return;
    }

    const badge =
        document.getElementById(statusId);

    element.classList.remove(
        "active-agent"
    );

    if (status === "running") {

        if (badge) {
            badge.innerText = "RUNNING";
            badge.className = "badge running";
        }

        element.classList.add(
            "active-agent"
        );
    }

    else if (status === "completed") {

        if (badge) {
            badge.innerText = "COMPLETED";
            badge.className = "badge completed";
        }
    }

    else {

        if (badge) {
            badge.innerText = "WAITING";
            badge.className = "badge waiting";
        }
    }

    const textElement =
        document.getElementById(textId);

    if (textElement && text !== undefined) {
        textElement.innerText = text;
    }
}


/* ---------------------------------------------------------
   ACTIVITY FEED
--------------------------------------------------------- */

function addActivity(
    icon,
    agent,
    message
) {

    const activity =
        document.getElementById(
            "activity"
        );

    if (!activity) return;

    const item =
        document.createElement("div");

    item.className =
        "activity-item";

    item.innerHTML = `
        <span>${icon}</span>
        <div>
            <strong>${agent}</strong>
            <p>${message}</p>
        </div>
    `;

    activity.prepend(item);
}


/* ---------------------------------------------------------
   AGENT ICON
--------------------------------------------------------- */

function getAgentIcon(agent) {

    if (agent === "IDENTITY")
        return "👤";

    if (agent === "NETWORK")
        return "🌐";

    if (agent === "ENDPOINT")
        return "💻";

    return "🤖";
}


/* ---------------------------------------------------------
   RESET
--------------------------------------------------------- */

function resetAgents() {

    const agents = [
        {
            key: "orchestrator",
            element: "orchestrator",
            status: "orchestrator-status"
        },
        {
            key: "identity",
            element: "identity-agent",
            status: "identity-status"
        },
        {
            key: "network",
            element: "network-agent",
            status: "network-status"
        },
        {
            key: "endpoint",
            element: "endpoint-agent",
            status: "endpoint-status"
        },
        {
            key: "resolution",
            element: "resolution-agent",
            status: "resolution-status"
        }
    ];

    agents.forEach(agent => {

        const status =
            document.getElementById(
                agent.status
            );

        if (status) {
            status.innerText =
                "WAITING";

            status.className =
                "badge waiting";
        }

        const element =
            document.getElementById(
                agent.element
            );

        if (element) {
            element.classList.remove(
                "active-agent"
            );
        }
    });

    const activity =
        document.getElementById(
            "activity"
        );

    if (activity) {
        activity.innerHTML = "";
    }

    const finalAnswer =
        document.getElementById(
            "final-answer"
        );

    if (finalAnswer) {
        finalAnswer.innerText =
            "Waiting for an IT request...";
    }
}


/* ---------------------------------------------------------
   DELAY
--------------------------------------------------------- */

function sleep(ms) {

    return new Promise(
        resolve =>
            setTimeout(resolve, ms)
    );
}

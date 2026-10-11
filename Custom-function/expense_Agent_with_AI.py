import json
import os

from dotenv import load_dotenv
from openai import OpenAI


# ============================================================
# 1. LOAD ENVIRONMENT VARIABLES
# ============================================================

load_dotenv()

AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
AZURE_OPENAI_DEPLOYMENT = os.getenv("AZURE_OPENAI_DEPLOYMENT")


if not AZURE_OPENAI_ENDPOINT:
    raise ValueError("AZURE_OPENAI_ENDPOINT is missing in .env")

if not AZURE_OPENAI_API_KEY:
    raise ValueError("AZURE_OPENAI_API_KEY is missing in .env")

if not AZURE_OPENAI_DEPLOYMENT:
    raise ValueError("AZURE_OPENAI_DEPLOYMENT is missing in .env")


# ============================================================
# 2. CREATE AZURE OPENAI CLIENT
# ============================================================

client = OpenAI(
    api_key=AZURE_OPENAI_API_KEY,
    base_url=AZURE_OPENAI_ENDPOINT.rstrip("/") + "/openai/v1/"
)


# ============================================================
# 3. COMPANY EXPENSE POLICY
# ============================================================

EXPENSE_POLICY = {
    "hotel": 5000,
    "taxi": 2000,
    "meals": 1500,
    "flight": 15000
}


# ============================================================
# 4. CUSTOM FUNCTION
# ============================================================

def check_expense_policy(expense_type, amount):
    """
    Custom business function.

    This function represents a real company system,
    database, API, or business rule engine.
    """

    expense_type = expense_type.lower().strip()

    maximum_allowed = EXPENSE_POLICY.get(expense_type)

    if maximum_allowed is None:
        return {
            "status": "UNKNOWN_EXPENSE_TYPE",
            "expense_type": expense_type,
            "amount": amount,
            "message": "This expense type is not defined in the company policy."
        }

    if amount <= maximum_allowed:
        status = "APPROVED"
        message = (
            f"The expense is within the company policy. "
            f"The maximum allowed amount for {expense_type} is ₹{maximum_allowed}."
        )
    else:
        status = "EXCEEDS_LIMIT"
        message = (
            f"The expense exceeds the company policy. "
            f"The maximum allowed amount for {expense_type} is ₹{maximum_allowed}."
        )

    return {
        "status": status,
        "expense_type": expense_type,
        "amount": amount,
        "maximum_allowed": maximum_allowed,
        "message": message
    }


# ============================================================
# 5. DEFINE CUSTOM FUNCTION FOR THE AI AGENT
# ============================================================

tools = [
    {
        "type": "function",
        "name": "check_expense_policy",
        "description": (
            "Check whether an employee expense is within "
            "the company reimbursement policy."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "expense_type": {
                    "type": "string",
                    "description": (
                        "Type of employee expense, such as "
                        "hotel, taxi, meals, or flight."
                    )
                },
                "amount": {
                    "type": "number",
                    "description": "Expense amount in Indian Rupees."
                }
            },
            "required": [
                "expense_type",
                "amount"
            ],
            "additionalProperties": False
        }
    }
]


# ============================================================
# 6. AGENT INSTRUCTIONS
# ============================================================

instructions = """
You are an Employee Expense Assistant.

Your job is to help employees understand whether their
expenses are eligible for reimbursement.

IMPORTANT RULE:

Whenever the user asks whether an expense can be claimed,
you MUST use the check_expense_policy function.

Do not guess or invent the company's expense limits.

After receiving the function result:

1. Explain whether the expense is approved.
2. Mention the expense amount.
3. Mention the maximum allowed amount.
4. Give a short, friendly explanation.

Keep the response simple and suitable for an employee.
"""


# ============================================================
# 7. ASK THE AI AGENT
# ============================================================

def ask_expense_agent(user_question):

    print("\n" + "=" * 60)
    print("USER")
    print("=" * 60)

    print(user_question)

    # --------------------------------------------------------
    # FIRST REQUEST
    # --------------------------------------------------------

    response = client.responses.create(
        model=AZURE_OPENAI_DEPLOYMENT,
        instructions=instructions,
        input=user_question,
        tools=tools,
        max_output_tokens=1200
    )

    # --------------------------------------------------------
    # COLLECT FUNCTION CALL OUTPUTS
    # --------------------------------------------------------

    tool_outputs = []

    for item in response.output:

        # ----------------------------------------------------
        # CHECK WHETHER AI REQUESTED A CUSTOM FUNCTION
        # ----------------------------------------------------

        if item.type == "function_call":

            print("\n" + "=" * 60)
            print("AI AGENT → CUSTOM FUNCTION")
            print("=" * 60)

            print(f"Function: {item.name}")

            # Parse arguments generated by the AI
            arguments = json.loads(item.arguments)

            print(
                "Arguments:",
                json.dumps(arguments, indent=2, ensure_ascii=False)
            )

            # ------------------------------------------------
            # EXECUTE OUR PYTHON FUNCTION
            # ------------------------------------------------

            if item.name == "check_expense_policy":

                function_result = check_expense_policy(
                    expense_type=arguments["expense_type"],
                    amount=arguments["amount"]
                )

            else:

                function_result = {
                    "status": "ERROR",
                    "message": f"Unknown function: {item.name}"
                }

            # ------------------------------------------------
            # DISPLAY FUNCTION RESULT
            # ------------------------------------------------

            print("\n" + "=" * 60)
            print("CUSTOM FUNCTION RESULT")
            print("=" * 60)

            print(
                json.dumps(
                    function_result,
                    indent=4,
                    ensure_ascii=False
                )
            )

            # ------------------------------------------------
            # IMPORTANT:
            #
            # We must return the result to the SAME
            # Responses API conversation.
            #
            # previous_response_id=response.id
            #
            # links this function output to the original
            # function call.
            # ------------------------------------------------

            tool_outputs.append(
                {
                    "type": "function_call_output",
                    "call_id": item.call_id,
                    "output": json.dumps(
                        function_result,
                        ensure_ascii=False
                    )
                }
            )

    # ========================================================
    # 8. SEND FUNCTION RESULT BACK TO GPT
    # ========================================================

    if tool_outputs:

        print("\n" + "=" * 60)
        print("CUSTOM FUNCTION → AI AGENT")
        print("=" * 60)

        final_response = client.responses.create(
            model=AZURE_OPENAI_DEPLOYMENT,

            # VERY IMPORTANT
            # Link this request to the previous response
            previous_response_id=response.id,

            # Send the function result back to the model
            input=tool_outputs,

            max_output_tokens=1200
        )

        # ====================================================
        # 9. DISPLAY FINAL AI RESPONSE
        # ====================================================

        print("\n" + "=" * 60)
        print("FINAL AI RESPONSE")
        print("=" * 60)

        print(final_response.output_text)

        return final_response.output_text

    # ========================================================
    # 10. IF NO FUNCTION WAS REQUIRED
    # ========================================================

    print("\n" + "=" * 60)
    print("AI RESPONSE")
    print("=" * 60)

    print(response.output_text)

    return response.output_text


# ============================================================
# 11. MAIN PROGRAM
# ============================================================

if __name__ == "__main__":

    print("\n")
    print("╔" + "═" * 58 + "╗")
    print("║" + " EMPLOYEE EXPENSE AI ASSISTANT ".center(58) + "║")
    print("╚" + "═" * 58 + "╝")

    print("\nCompany Expense Policy:")
    print("-----------------------")
    print("Hotel  : ₹5,000")
    print("Taxi   : ₹2,000")
    print("Meals  : ₹1,500")
    print("Flight : ₹15,000")

    print("\nType your expense question.")
    print("Type 'exit' to quit.")

    while True:

        user_question = input("\nYou: ")

        if user_question.lower().strip() == "exit":
            print("\nGoodbye!")
            break

        if not user_question.strip():
            continue

        try:

            ask_expense_agent(user_question)

        except Exception as e:

            print("\n" + "=" * 60)
            print("ERROR")
            print("=" * 60)

            print(str(e))
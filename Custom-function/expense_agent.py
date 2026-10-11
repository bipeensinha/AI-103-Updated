def check_expense_policy(
    expense_type: str,
    amount: float
):
    
    policy = {
        "hotel": 5000,
        "taxi": 2000,
        "meals": 1500,
        "flight": 15000
    }

    expense_type = expense_type.lower()

    if expense_type not in policy:
        return {
            "status": "UNKNOWN",
            "message": f"No policy found for {expense_type}"
        }

    limit = policy[expense_type]

    if amount <= limit:
        status = "APPROVED"
    else:
        status = "REJECTED"

    return {
        "expense_type": expense_type,
        "amount": amount,
        "maximum_allowed": limit,
        "status": status
    }

result = check_expense_policy(
    "hotel",
    2500
)

print(result)
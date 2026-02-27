from typing import Any
from google.adk.tools import FunctionTool

def calculate_trip_budget(destination: str, days: int, style: str) -> dict[str, Any]:
    """Calculates estimated budget for a trip.

    Use this tool when the user asks about trip costs or budget estimates.

    Args:
        destination: The destination city or country
        days: Number of days for the trip
        style: Travel style (budget, mid-range, luxury)

    Returns:
        A dictionary with budget breakdown.
        Example: {'status': 'success', 'total': 3000, 'daily': 500, 'currency': 'USD'}
    """
    daily_rates = {"budget": 100, "mid-range": 250, "luxury": 500}

    daily = daily_rates.get(style.lower(), 250)
    total = daily * days

    return {
        "status": "success",
        "total": total,
        "daily": daily,
        "currency": "USD",
        "breakdown": {
            "accommodation": daily * 0.4,
            "food": daily * 0.3,
            "activities": daily * 0.2,
            "transport": daily * 0.1,
        },
    }

budget_tool = FunctionTool(func=calculate_trip_budget)

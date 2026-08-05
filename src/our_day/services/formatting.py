def format_currency(value: float) -> str:
    return f"{round(value):,.0f} Ft".replace(",", " ")

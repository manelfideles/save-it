import pandas as pd


def format_expenses_df(
    data: pd.DataFrame,
    cols: list[str] = ["type", "id", "title", "category", "amount", "date"],
) -> pd.DataFrame:
    formatted_data = data[cols]
    formatted_data["date"] = pd.to_datetime(formatted_data["date"], format="%Y-%m-%d")
    formatted_data["formatted_amount"] = formatted_data["amount"].apply(
        lambda x: f"€{x:.2f}"
    )
    return formatted_data

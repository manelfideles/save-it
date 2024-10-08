import os
from datetime import datetime
from functools import partial, wraps
from typing import Callable, ParamSpec, TypeVar

import pandas as pd
from dotenv import load_dotenv
from postgrest.base_request_builder import APIResponse
from pydantic import FilePath
from supabase import Client, create_client

load_dotenv()

supabase_url = os.environ.get("SUPABASE_URL")
supabase_key = os.environ.get("SUPABASE_KEY")

P = ParamSpec("P")
R = TypeVar("R")


class SupabaseClient:
    def __init__(self, url=supabase_url, key=supabase_key) -> None:
        self.client: Client = create_client(url, key)

    def load_categories(self) -> list[str]:
        response = self.client.table("categories").select("id,name").execute()
        return [c for c in response.data]

    def add_category(self, category: str):
        return self.client.table("categories").insert({"name": category}).execute()

    def save_entry(
        self,
        type: str,
        title: str,
        category: str,
        amount: float,
        date: datetime,
    ) -> APIResponse:
        date_str = date.strftime("%d-%m-%Y")
        response = (
            self.client.table("expenses")
            .insert(
                {
                    "type": type,
                    "title": title,
                    "category": category,
                    "amount": amount,
                    "date": date_str,
                }
            )
            .execute()
        )
        return response

    def delete_entry(self, entry_id: int):
        response = self.client.table("expenses").delete().eq("id", entry_id).execute()
        return response

    def update_entry(self, entry_id: int, updated_data: dict[str, str]) -> APIResponse:
        response = (
            self.client.table("expenses")
            .update(updated_data)
            .eq("id", entry_id)
            .execute()
        )
        print(response.data)
        return response

    def load_data(self) -> pd.DataFrame:
        response: APIResponse = self.client.rpc(
            "get_expenses_with_categories"
        ).execute()
        return pd.DataFrame(response.data)

    def process_csv(self, csv_file: FilePath):
        df = pd.read_csv(csv_file)
        for _, row in df.iterrows():
            self.save_entry(
                row["type"],
                row["title"],
                row["category"],
                row["amount"],
                datetime.strptime(row["date"], "%d-%m-%Y"),
            )


supabase_client = SupabaseClient()


def with_supabase_client(client: SupabaseClient = supabase_client):
    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        @wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            return partial(func, client)(*args, **kwargs)

        return wrapper

    return decorator

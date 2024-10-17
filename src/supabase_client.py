import os
from datetime import datetime
from functools import partial, wraps
from typing import Callable, ParamSpec, TypeVar

import pandas as pd
from dotenv import load_dotenv
from postgrest.base_request_builder import APIResponse
from pydantic import FilePath
from supabase import Client, create_client

from utils import format_expenses_df

load_dotenv()

supabase_url = os.environ.get("SUPABASE_URL")
supabase_key = os.environ.get("SUPABASE_KEY")

P = ParamSpec("P")
R = TypeVar("R")


class SupabaseClient:
    def __init__(self, url=supabase_url, key=supabase_key) -> None:
        self.client: Client = create_client(url, key)

    def load_categories(self) -> pd.DataFrame:
        response = self.client.table("categories").select("id,name").execute()
        categories = pd.DataFrame(response.data)
        return categories

    def add_category(self, category: str):
        return self.client.table("categories").insert({"name": category}).execute()

    def save_entry(
        self,
        type: str,
        title: str,
        category_id: str,
        amount: float,
        date: str | datetime,
    ) -> APIResponse:
        try:
            date_str = date.isoformat()
        except AttributeError:
            date_str = date

        response = (
            self.client.table("expenses")
            .insert(
                {
                    "type": type,
                    "title": title,
                    "category": category_id,
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
        return response

    def load_data(self) -> pd.DataFrame:
        response: APIResponse = self.client.rpc(
            "get_expenses_with_categories"
        ).execute()
        data = pd.DataFrame(response.data)
        formatted_data = format_expenses_df(data)
        return formatted_data

    def process_csv(self, csv_file: FilePath):
        df = pd.read_csv(csv_file)
        categories = self.load_categories()
        response = None
        for _, row in df.iterrows():
            category_id = categories[categories["name"] == row["category"]][
                "id"
            ].to_list()[0]
            response = self.save_entry(
                row["type"],
                row["title"],
                category_id,
                row["amount"],
                row["date"],
            )
        return response


supabase_client = SupabaseClient()


def with_supabase_client(client: SupabaseClient = supabase_client):
    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        @wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            return partial(func, client)(*args, **kwargs)

        return wrapper

    return decorator

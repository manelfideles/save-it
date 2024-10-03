import os
from datetime import datetime

import pandas as pd
from dotenv import load_dotenv
from pydantic import FilePath
from supabase import Client, create_client

load_dotenv()

supabase_url = os.environ.get("SUPABASE_URL")
supabase_key = os.environ.get("SUPABASE_KEY")


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
    ) -> None:
        date_str = date.strftime("%d-%m-%Y")
        self.client.table("expenses").insert(
            {
                "type": type,
                "title": title,
                "category": category,
                "amount": amount,
                "date": date_str,
            }
        ).execute()

    def load_data(self) -> pd.DataFrame:
        response = self.client.rpc("get_expenses_with_categories").execute()
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

    def delete_entry(self, entry_id: int):
        self.client.table("expenses").delete().eq("id", entry_id).execute()

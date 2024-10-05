import pandas as pd
import streamlit as st

from supabase_client import SupabaseClient
from ui import expense_table, report

supabase_client = SupabaseClient()


def expenses_page():
    st.header("My Expenses")
    data = supabase_client.load_data()
    cols = ["type", "id", "title", "category", "amount", "date"]
    expenses = data[data["type"] == "Expense"][cols]

    expenses["date"] = pd.to_datetime(expenses["date"], format="%Y-%d-%m")
    expenses["formatted_date"] = expenses["date"].dt.strftime("%Y-%d-%m")
    expenses["formatted_amount"] = expenses["amount"].apply(lambda x: f"€{x:.2f}")

    table_col, report_col = st.columns(2)
    with table_col:
        expenses = expense_table(supabase_client, expenses)
    with report_col:
        incomes = data[data["type"] == "Income"]
        report(incomes, expenses)


def add_entry_page():
    st.header("Add New Entry")
    categories = supabase_client.load_categories()
    entry_type = st.radio("Type", ["Expense", "Income"])
    title = st.text_input("Title")
    category = st.selectbox("Category", [cat["name"] for cat in categories])
    amount = st.number_input("Amount", min_value=0.0, format="%.2f")
    date = st.date_input("Date", format="DD/MM/YYYY")

    if st.button("Save Entry"):
        if all([title, category, amount, date]):
            category_id = next(
                cat["id"] for cat in categories if cat["name"] == category
            )
            supabase_client.save_entry(
                entry_type,
                title,
                category_id,
                amount,
                date,
            )
            st.success("Entry saved successfully!")
        else:
            st.error("Please fill all fields")


def upload_csv_page():
    st.header("Upload CSV File")
    uploaded_file = st.file_uploader("Choose a CSV file", type="csv")
    if uploaded_file is not None:
        supabase_client.process_csv(uploaded_file)
        st.success("CSV processed successfully!")

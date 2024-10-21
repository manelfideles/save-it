from time import sleep

import pandas as pd
import streamlit as st

from supabase_client import SupabaseClient, with_supabase_client
from ui import make_expenses_table, make_report


@with_supabase_client()
def expenses_page(client: SupabaseClient):
    st.header("My Expenses")
    data = client.load_data()
    if not data.empty:
        expenses = data[data["type"] == "Expense"]
        incomes = data[data["type"] == "Income"]
        table_col, report_col = st.columns([0.4, 0.6])
        with table_col:
            expenses = make_expenses_table(expenses)
        with report_col:
            make_report(incomes, expenses)
    else:
        st.info("No data to display.")


@with_supabase_client()
def add_entry_page(client: SupabaseClient):
    st.header("Add New Entry")
    categories = client.load_categories()
    entry_type = st.radio("Type", ["Expense", "Income"])
    title = st.text_input("Title")
    category = st.selectbox("Category", categories["name"].to_list())
    amount = st.number_input("Amount", min_value=0.0, format="%.2f")
    date = st.date_input("Date", format="YYYY/MM/DD")
    if st.button("Save Entry"):
        if all([title, category, amount, date]):
            category_id = int(
                categories[categories["name"] == category]["id"].to_list()[0]
            )
            response = client.save_entry(entry_type, title, category_id, amount, date)
            if response.data:
                st.success("Entry saved successfully!")
        else:
            st.error("Please fill all fields")


@with_supabase_client()
def upload_csv_page(client: SupabaseClient):
    st.header("Upload CSV File")
    uploaded_file = st.file_uploader("Choose a CSV file", type="csv")
    if uploaded_file is not None:
        client.process_csv(uploaded_file)
        st.success("CSV processed successfully!")

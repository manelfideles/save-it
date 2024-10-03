from datetime import datetime

import pandas as pd
import plotly.express as px
import streamlit as st

from supabase_client import SupabaseClient

supabase_client = SupabaseClient()


def expenses_page():
    st.header("Expenses")
    data = supabase_client.load_data()
    cols = ["id", "title", "category", "amount", "date"]
    expenses = data[data["type"] == "Expense"][cols]

    expenses["date"] = pd.to_datetime(expenses["date"], format="%Y-%d-%m")
    expenses["formatted_date"] = expenses["date"].dt.strftime("%Y-%d-%m")
    expenses["formatted_amount"] = expenses["amount"].apply(lambda x: f"€{x:.2f}")

    sort_column = st.selectbox(
        "Sort by:",
        options=cols,
        format_func=lambda x: dict(zip(cols, [s.capitalize() for s in cols]))[x],
    )
    sort_order = st.radio("Sort order:", ("Ascending", "Descending"), horizontal=True)
    ascending = sort_order == "Ascending"
    if sort_column == "amount":
        expenses = expenses.sort_values("amount", ascending=ascending)
    elif sort_column == "date":
        expenses = expenses.sort_values("date", ascending=ascending)
    else:
        expenses = expenses.sort_values(sort_column, ascending=ascending)

    # Display table with delete buttons
    for _, row in expenses.iterrows():
        col1, col2, col3, col4, col5, col6 = st.columns([1, 2, 2, 2, 2, 1])

        with col1:
            st.write(row["id"])
        with col2:
            st.write(row["title"])
        with col3:
            st.write(row["category"])
        with col4:
            st.write(row["formatted_date"])
        with col5:
            st.write(row["formatted_amount"])
        with col6:
            if st.button("🗑️", key=f"delete_{row['id']}", help="Delete this entry"):
                supabase_client.delete_entry(row["id"])
                st.rerun()


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


def reports_page():
    st.header("Expense Reports")
    data = supabase_client.load_data()
    if not data.empty:
        data["date"] = pd.to_datetime(data["date"], format="%Y-%d-%m")

        # Calculate current month's totals
        current_month = datetime.now().replace(day=1).strftime("%Y-%d-%m")
        current_month = pd.to_datetime(current_month, format="%Y-%d-%m")
        current_month_data = data[data["date"] >= current_month]
        total_income = current_month_data[current_month_data["type"] == "Income"][
            "amount"
        ].sum()
        total_expenses = current_month_data[current_month_data["type"] == "Expense"][
            "amount"
        ].sum()

        # Calculate previous month's totals
        prev_month = current_month - pd.DateOffset(months=1)
        prev_month_data = data[
            (data["date"] >= prev_month) & (data["date"] < current_month)
        ]
        prev_income = prev_month_data[prev_month_data["type"] == "Income"][
            "amount"
        ].sum()
        prev_expenses = prev_month_data[prev_month_data["type"] == "Expense"][
            "amount"
        ].sum()

        # Savings
        savings = total_income - total_expenses
        prev_savings = prev_income - prev_expenses

        # Display stats
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric(
                "Total Income",
                f"€{total_income:.2f}",
                f"€{total_income - prev_income:.2f}",
            )
        with col2:
            st.metric(
                "Total Expenses",
                f"€{total_expenses:.2f}",
                f"€{total_expenses - prev_expenses:.2f}",
            )
        with col3:
            st.metric(
                "Savings",
                f"€{savings:.2f}",
                f"€{prev_savings:.2f}",
            )

        # Create bar chart
        expenses_by_category = (
            data[data["type"] == "Expense"]
            .groupby("category")["amount"]
            .sum()
            .reset_index()
        )
        fig = px.bar(
            expenses_by_category,
            x="category",
            y="amount",
            title="Expenses by Category",
        )
        st.plotly_chart(fig)
    else:
        st.info("No data available for reporting")

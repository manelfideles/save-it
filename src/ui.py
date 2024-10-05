from datetime import datetime, timedelta

import pandas as pd
import plotly.express as px
import streamlit as st
from streamlit_modal import Modal

from supabase_client import SupabaseClient


def expense_table(supabase_client: SupabaseClient, expenses: pd.DataFrame):
    st.subheader("Filters")
    categories = list(expenses["category"].unique())
    col1, col2 = st.columns(2)
    with col1:
        # Date range filter
        date_filter = st.selectbox(
            "Date Range",
            [
                "All Time",
                "Last 7 Days",
                "Last 30 Days",
                "Last 90 Days",
                "Custom Range",
            ],
        )

        if date_filter == "Custom Range":
            start_date = st.date_input("Start Date")
            end_date = st.date_input("End Date")
            expenses = expenses[
                (expenses["date"].dt.date >= start_date)
                & (expenses["date"].dt.date <= end_date)
            ]
        elif date_filter != "All Time":
            days = {"Last 7 Days": 7, "Last 30 Days": 30, "Last 90 Days": 90}
            cutoff_date = (datetime.now() - timedelta(days=days[date_filter])).strftime(
                "%Y-%m-%d"
            )
            expenses = expenses[expenses["date"] >= cutoff_date]
    with col2:
        selected_categories = st.multiselect(
            "Categories",
            options=categories,
            default=categories,  # All categories selected by default
            help="Select one or more categories",
        )
        if selected_categories:
            expenses = expenses[expenses["category"].isin(selected_categories)]

    search_term = st.text_input("Search entries", "")
    if search_term:
        expenses = expenses[
            expenses["title"].str.contains(search_term, case=False)
            | expenses["category"].str.contains(search_term, case=False)
        ]

    col1, col2 = st.columns(2)
    with col1:
        sort_column = st.selectbox(
            "Sort by:",
            options=["date", "amount", "title", "category", "type"],
            format_func=lambda x: {
                "date": "Date",
                "amount": "Amount",
                "title": "Title",
                "category": "Category",
                "type": "Type",
            }[x],
        )
    with col2:
        sort_order = st.radio(
            "Sort order:", ("Ascending", "Descending"), horizontal=True
        )

    ascending = sort_order == "Ascending"
    if sort_column == "amount":
        expenses = expenses.sort_values("amount", ascending=ascending)
    elif sort_column == "date":
        expenses = expenses.sort_values("date", ascending=ascending)
    else:
        expenses = expenses.sort_values(sort_column, ascending=ascending)

    for _, row in expenses.iterrows():
        with st.expander(
            f"{row['title']} - {row['formatted_amount']} ({row['formatted_date']})"
        ):
            col1, col2, col3 = st.columns([3, 1, 1])
            with col1:
                st.write(f"**Category:** {row['category']}")
                st.write(f"**Type:** {row['type']}")
            with col2:
                if st.button("Edit 📝", key=f"edit_{row['id']}"):
                    edit_modal = Modal("Edit Entry", key=f"edit_modal_{row['id']}")
                    with edit_modal.container():
                        edited_title = st.text_input("Title", value=row["title"])
                        edited_amount = st.number_input(
                            "Amount", value=float(row["amount"])
                        )
                        edited_category = st.selectbox(
                            "Category",
                            categories[1:],
                            index=categories[1:].index(row["category"]),
                        )
                        edited_type = st.selectbox(
                            "Type",
                            ["Income", "Expense"],
                            index=0 if row["type"] == "1" else 1,
                        )
                        edited_date = st.date_input("Date", value=row["date"])

                        if st.button("Save Changes"):
                            updated_data = {
                                "title": edited_title,
                                "amount": edited_amount,
                                "category": categories.index(edited_category),
                                "type": "1" if edited_type == "Income" else "-1",
                                "date": edited_date.strftime("%Y-%d-%m"),
                            }
                            supabase_client.update_entry(row["id"], updated_data)
                            st.success("Entry updated successfully!")
                            st.experimental_rerun()
            with col3:
                if st.button("Delete 🗑️", key=f"delete_{row['id']}"):
                    confirm_modal = Modal(
                        "Confirm Deletion", key=f"confirm_modal_{row['id']}"
                    )
                    with confirm_modal.container():
                        st.write("Are you sure you want to delete this entry?")
                        col1, col2 = st.columns(2)
                        with col1:
                            if st.button("Yes, delete"):
                                supabase_client.delete_entry(row["id"])
                                st.success("Entry deleted successfully!")
                                st.rerun()
                        with col2:
                            if st.button("Cancel"):
                                confirm_modal.close()
    return expenses


def report(incomes: pd.DataFrame, expenses: pd.DataFrame):
    if not expenses.empty:
        incomes["date"] = pd.to_datetime(incomes["date"], format="%Y-%d-%m")
        expenses["date"] = pd.to_datetime(expenses["date"], format="%Y-%d-%m")
        current_month = datetime.now().replace(day=1).strftime("%Y-%d-%m")
        current_month = pd.to_datetime(current_month, format="%Y-%d-%m")
        stats = calculate_stats(incomes, expenses, current_month)
        render_stats(stats)

        expenses_by_category = (
            expenses[expenses["type"] == "Expense"]
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


def calculate_stats(incomes: pd.DataFrame, expenses: pd.DataFrame, current_month):
    current_month_incomes = incomes[incomes["date"] >= current_month]
    current_month_expenses = expenses[expenses["date"] >= current_month]
    total_income = current_month_incomes["amount"].sum()
    total_expenses = current_month_expenses["amount"].sum()

    prev_month = current_month - pd.DateOffset(months=1)
    prev_month_incomes = incomes[
        (incomes["date"] >= prev_month) & (incomes["date"] < current_month)
    ]
    prev_month_expenses = expenses[
        (expenses["date"] >= prev_month) & (expenses["date"] < current_month)
    ]
    prev_income = prev_month_incomes[prev_month_incomes["type"] == "Income"][
        "amount"
    ].sum()
    prev_expenses = prev_month_expenses[prev_month_expenses["type"] == "Expense"][
        "amount"
    ].sum()
    savings = total_income - total_expenses
    prev_savings = prev_income - prev_expenses
    return {
        "total_income": total_income,
        "total_expenses": total_expenses,
        "prev_income": prev_income,
        "prev_expenses": prev_expenses,
        "savings": savings,
        "prev_savings": prev_savings,
    }


def render_stats(stats: dict):
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(
            "Total Income",
            f"€{stats['total_income']:.2f}",
            f"€{stats['total_income'] - stats['prev_income']:.2f}",
        )
    with col2:
        st.metric(
            "Total Expenses",
            f"€{stats['total_expenses']:.2f}",
            f"€{stats['total_expenses'] - stats['prev_expenses']:.2f}",
        )
    with col3:
        st.metric(
            "Savings",
            f"€{stats['savings']:.2f}",
            f"€{stats['prev_savings']:.2f}",
        )

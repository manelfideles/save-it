from datetime import datetime, timedelta

import pandas as pd
import plotly.express as px
import streamlit as st

from supabase_client import SupabaseClient, with_supabase_client


def filter_by_date_range(expenses: pd.DataFrame):
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
    return expenses


def filter_by_category(expenses: pd.DataFrame, categories: list[str]):
    with st.container():
        selected_categories = st.multiselect("Categories", categories, default=None)
        if selected_categories:
            expenses = expenses[expenses["category"].isin(selected_categories)]
        return expenses


def sort_expenses_by(expenses: pd.DataFrame):
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
            "Sort order:", ("Descending", "Ascending"), horizontal=True
        )
    ascending = sort_order == "Ascending"
    if sort_column == "amount":
        expenses = expenses.sort_values("amount", ascending=ascending)
    elif sort_column == "date":
        expenses = expenses.sort_values("date", ascending=ascending)
    else:
        expenses = expenses.sort_values(sort_column, ascending=ascending)
    return expenses


def filter_expenses(expenses: pd.DataFrame, categories: list[str]) -> pd.DataFrame:
    col1, col2 = st.columns(2)
    with col1:
        expenses = filter_by_date_range(expenses)
    with col2:
        expenses = filter_by_category(expenses, categories)
    expenses = sort_expenses_by(expenses)
    return expenses


@with_supabase_client()
def make_expenses_table(client: SupabaseClient, expenses: pd.DataFrame):
    def _center_align_row_html(row) -> str:
        style = "margin-top: 5px; width: 100%;"
        return f"<div style='{style}'>{row}</div>"

    categories = list(expenses["category"].unique())
    expenses = filter_expenses(expenses, categories)

    expenses["date"] = expenses["date"].dt.date
    for _, row in expenses.iterrows():
        col1, col2, col3, col4, col5 = st.columns([2, 2, 2, 1, 1])
        with col1:
            st.markdown(_center_align_row_html(row["title"]), unsafe_allow_html=True)
        with col2:
            st.markdown(_center_align_row_html(row["category"]), unsafe_allow_html=True)
        with col3:
            st.markdown(_center_align_row_html(row["date"]), unsafe_allow_html=True)
        with col4:
            st.markdown(
                _center_align_row_html(row["formatted_amount"]), unsafe_allow_html=True
            )
        with col5:
            if st.button("🗑️", key=f"delete_{row['id']}", help="Delete this entry"):
                response = client.delete_entry(row["id"])
                if response.data:
                    st.rerun()
                else:
                    st.error(f"Entry #{str(row['id'])} could not be deleted.")
    return expenses


def make_report(incomes: pd.DataFrame, expenses: pd.DataFrame):
    if not expenses.empty:
        incomes.loc[:, "date"] = pd.to_datetime(incomes["date"], format="%Y-%m-%d")
        expenses.loc[:, "date"] = pd.to_datetime(expenses["date"], format="%Y-%m-%d")
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

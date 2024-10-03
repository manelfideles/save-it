import streamlit as st

import pages

if __name__ == "__main__":
    st.title("Expense Tracker")
    tab1, tab2, tab3, tab4 = st.tabs(
        [
            "Add Entry",
            "Expenses",
            "Upload CSV",
            "Reports",
        ]
    )
    with tab1:
        pages.add_entry_page()
    with tab2:
        pages.expenses_page()
    with tab3:
        pages.upload_csv_page()
    with tab4:
        pages.reports_page()

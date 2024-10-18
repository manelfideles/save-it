import streamlit as st

import pages
from auth import Authenticator

if __name__ == "__main__":
    st.set_page_config(page_title="Expense Tracker", page_icon="💰", layout="wide")
    st.title("Expense Tracker")
    auth = Authenticator()
    auth.check_authentication()
    auth.logout()

    tab1, tab2, tab3 = st.tabs(["Add Entry", "My Expenses", "Upload CSV"])
    with tab1:
        pages.add_entry_page()
    with tab2:
        pages.expenses_page()
    with tab3:
        pages.upload_csv_page()

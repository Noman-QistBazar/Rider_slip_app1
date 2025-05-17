import streamlit as st
from modules import utils, admin, branch
from supabase_client import supabase

st.set_page_config(page_title="Delivery Slip Portal", layout="centered")

st.title("🚚 Delivery Slip Submission Portal")

branch_code = st.text_input("Enter Branch Code")

if branch_code:
    if branch_code.upper() == "ADMIN2024":
        admin.render_admin_panel()
    elif utils.validate_branch_code(branch_code):
        branch.render_branch_panel(branch_code)
    else:
        st.error("Invalid branch code. Please try again.")

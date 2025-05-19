import streamlit as st
from modules import utils, admin, branch
from supabase_client import supabase
from PIL import Image

st.set_page_config(page_title="Delivery Slip Portal", layout="centered")

# Logo
logo = Image.open("data/QB-logo.png")
with st.container():
    st.markdown("<div style='text-align: center;'>", unsafe_allow_html=True)
    st.image(logo, use_container_width=False, width=250)
    st.markdown("</div>", unsafe_allow_html=True)

st.title("🚚 Delivery Slip Submission Portal")

branch_code = st.text_input("Enter Branch Code")

if branch_code:
    if branch_code.upper() == "ADMIN2024":
        admin.render_admin_panel()
    elif utils.validate_branch_code(branch_code):
        branch.render_branch_panel(branch_code)
    else:
        st.error("Invalid branch code. Please try again.")

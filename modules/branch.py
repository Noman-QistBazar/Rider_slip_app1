import streamlit as st
from supabase_client import supabase
from modules.utils import hash_image
import datetime
import calendar


def get_weeks_of_month(year, month):
    weeks = []
    cal = calendar.Calendar(firstweekday=calendar.MONDAY)
    month_days = list(cal.itermonthdates(year, month))

    week_start = None
    week_end = None
    current_week = []

    for day in month_days:
        if day.month != month:
            continue

        if week_start is None:
            week_start = day

        current_week.append(day)

        # If Sunday or last day of month, close the week
        if day.weekday() == 6 or day == max(
            [d for d in month_days if d.month == month]
        ):
            week_end = day
            weeks.append((week_start, week_end))
            week_start = None
            current_week = []

    return weeks


def render_branch_panel(code):
    # Fetch branch data
    branch_data = (
        supabase.table("branches")
        .select("*")
        .eq("code", code.upper())
        .single()
        .execute()
        .data
    )

    branch_name = branch_data.get("name") if branch_data else "Unknown Branch"

    st.header(f"Branch Panel - {branch_name}")

    today = datetime.date.today()
    weeks = get_weeks_of_month(today.year, today.month)

    week_options = [
        f"{w[0].strftime('%d %b %Y')} - {w[1].strftime('%d %b %Y')}" for w in weeks
    ]
    week = st.selectbox("Select Week", week_options)

    slip_type = st.radio("Slip Type", ["Cash Slip", "Online Slip"])
    qty = st.number_input("Slip Quantity", min_value=1, step=1)
    img = st.file_uploader("Upload Slip Image", type=["jpg", "jpeg", "png"])

    riders = branch_data["riders"] if branch_data and "riders" in branch_data else []
    rider = st.selectbox("Rider Name", riders)

    ids = []
    if slip_type == "Online Slip":
        for i in range(qty):
            ids.append(st.text_input(f"Transaction ID #{i+1}", key=f"tid_{i}"))
    else:
        for i in range(qty):
            ids.append(st.text_input(f"Serial Number #{i+1}", key=f"sid_{i}"))

    commission = qty * (50 if slip_type == "Online Slip" else 25)
    st.info(f"Total Commission: Rs. {commission}")

    if st.button("Submit Slip"):
        if img is None:
            st.error("Please upload an image.")
            return
        img_hash = hash_image(img)
        existing = (
            supabase.table("slips")
            .select("img_hash")
            .eq("img_hash", img_hash)
            .execute()
            .data
        )
        if existing:
            st.error("This image has already been uploaded.")
            return

        slip_data = {
            "branch_code": code.upper(),
            "week": week,
            "type": slip_type,
            "qty": qty,
            "rider": rider,
            "ids": ids,
            "img_hash": img_hash,
            "commission": commission,
            "timestamp": str(datetime.datetime.now()),
        }
        supabase.table("slips").insert(slip_data).execute()
        st.success("Slip submitted successfully!")

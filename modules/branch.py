import streamlit as st
from supabase_client import supabase
from modules.utils import hash_image
import datetime
import calendar
import io

# Utility to get weeks of the current month
def get_weeks_of_month(year, month):
    weeks = []
    cal = calendar.Calendar(firstweekday=calendar.MONDAY)
    month_days = list(cal.itermonthdates(year, month))

    week_start = None
    for day in month_days:
        if day.month != month:
            continue
        if week_start is None:
            week_start = day
        if day.weekday() == 6 or day == max([d for d in month_days if d.month == month]):
            week_end = day
            weeks.append((week_start, week_end))
            week_start = None

    return weeks

# Main branch panel UI
def render_branch_panel(code):
    # Get branch data
    branch_data = supabase.table("branches").select("*").eq("code", code.upper()).single().execute().data
    branch_name = branch_data.get("name") if branch_data else "Unknown Branch"

    st.header(f"Branch Panel - {branch_name}")

    today = datetime.date.today()
    weeks = get_weeks_of_month(today.year, today.month)
    week_options = [f"{w[0].strftime('%d %b %Y')} - {w[1].strftime('%d %b %Y')}" for w in weeks]
    default_week = week_options[0] if week_options else ""
    week = st.selectbox("Select Week", week_options, index=0 if week_options else None)

    slip_type = st.radio("Slip Type", ["Cash Slip", "Online Slip"], key="slip_type")
    qty = st.number_input("Slip Quantity", min_value=1, step=1, key="qty")

    riders = branch_data["riders"] if branch_data and "riders" in branch_data else []
    rider = st.selectbox("Rider Name", riders, key="rider")

    ids = []
    for i in range(qty):
        ids.append(
            st.text_input(
                f"{'Transaction ID' if slip_type == 'Online Slip' else 'Serial Number'} #{i+1}",
                key=f"id_{i}"
            )
        )

    commission = qty * (50 if slip_type == "Online Slip" else 25)
    st.info(f"Total Commission: Rs. {commission}")

    img = st.file_uploader("Upload Slip Image", type=["jpg", "jpeg", "png"], key="img")

    if "draft_slips" not in st.session_state:
        st.session_state.draft_slips = []
    if "editing_index" not in st.session_state:
        st.session_state.editing_index = None

    if st.button("Add to List"):
        if img is None:
            st.error("Please upload an image.")
            return

        img_bytes = img.read()
        img_hash = hash_image(io.BytesIO(img_bytes))
        existing_hashes = [entry["img_hash"] for entry in st.session_state.draft_slips]
        if img_hash in existing_hashes:
            st.error("This image has already been added.")
            return

        slip_data = {
            "branch_code": code.upper(),
            "week": week,
            "type": slip_type,
            "qty": qty,
            "rider": rider,
            "ids": ids,
            "img": img_bytes,
            "img_name": img.name,
            "img_hash": img_hash,
            "commission": commission,
            "timestamp": str(datetime.datetime.now())
        }

        st.session_state.draft_slips.append(slip_data)
        st.success("Slip added to draft list.")

        # Reset inputs
        for i in range(qty):
            st.session_state.pop(f"id_{i}", None)
        st.session_state.pop("img", None)
        st.session_state.pop("rider", None)
        st.session_state.pop("qty", None)
        st.session_state.pop("slip_type", None)
        st.rerun()

    if st.session_state.draft_slips:
        st.subheader("Draft Slips")

        for idx, slip in enumerate(st.session_state.draft_slips):
            col1, col2, col3, col4 = st.columns([3, 3, 1, 1])
            transaction_ids = ", ".join(slip["ids"])
            col1.markdown(f"**{slip['rider']}** - {slip['type']} - {slip['qty']} slips<br><small>{transaction_ids}</small>", unsafe_allow_html=True)
            col2.markdown(slip["week"])
            if col3.button("✏️", key=f"edit_{idx}"):
                st.session_state.editing_index = idx
            if col4.button("🗑️", key=f"delete_{idx}"):
                st.session_state.draft_slips.pop(idx)
                st.rerun()

        if st.session_state.editing_index is not None:
            st.markdown("---")
            st.subheader("Edit Slip (Currently Editing)")
            slip = st.session_state.draft_slips[st.session_state.editing_index]
            new_qty = st.number_input("Slip Quantity", min_value=1, value=slip["qty"], key="edit_qty")
            new_rider = st.text_input("Rider Name", value=slip["rider"], key="edit_rider")
            new_type = st.radio("Slip Type", ["Cash Slip", "Online Slip"], index=0 if slip["type"] == "Cash Slip" else 1, key="edit_type")
            new_ids = []
            for i in range(new_qty):
                new_ids.append(st.text_input(f"{'Transaction ID' if new_type == 'Online Slip' else 'Serial Number'} #{i+1}", value=slip["ids"][i] if i < len(slip["ids"]) else "", key=f"edit_id_{i}"))

            if st.button("Save Changes"):
                slip["qty"] = new_qty
                slip["rider"] = new_rider
                slip["type"] = new_type
                slip["ids"] = new_ids
                slip["commission"] = new_qty * (50 if new_type == "Online Slip" else 25)
                st.session_state.draft_slips[st.session_state.editing_index] = slip
                st.session_state.editing_index = None
                st.success("Slip updated.")

            if st.button("Cancel Edit"):
                st.session_state.editing_index = None

        if st.button("Submit All Slips"):
            # Fetch already-submitted image hashes from Supabase
            result = supabase.table("slips").select("img_hash").execute()
            submitted_hashes = set()
            if result.data:
                submitted_hashes = {s["img_hash"] for s in result.data if "img_hash" in s}

            to_submit = []
            skipped = 0

            for slip in st.session_state.draft_slips:
                if slip["img_hash"] in submitted_hashes:
                    st.warning(f"Skipped duplicate for rider **{slip['rider']}** – this slip was already submitted.")
                    skipped += 1
                    continue
                to_submit.append(slip)

            for slip in to_submit:
                supabase.table("slips").insert({
                    "branch_code": slip["branch_code"],
                    "week": slip["week"],
                    "type": slip["type"],
                    "qty": slip["qty"],
                    "rider": slip["rider"],
                    "ids": slip["ids"],
                    "img_hash": slip["img_hash"],
                    "commission": slip["commission"],
                    "timestamp": slip["timestamp"]
                }).execute()

            st.success(f"{len(to_submit)} slips submitted to Supabase successfully!")
            if skipped:
                st.info(f"{skipped} duplicate slip(s) were skipped.")

            st.session_state.draft_slips = [slip for slip in st.session_state.draft_slips if slip["img_hash"] in submitted_hashes]
            st.rerun()

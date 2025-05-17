import streamlit as st
from supabase_client import supabase
import datetime


def render_admin_panel():
    st.header("Admin Panel")
    tab1, tab2, tab3 = st.tabs(["Manage Branches", "Manage Riders", "Change Requests"])

    # --------- Branch Management ---------
    with tab1:
        st.subheader("Branches")
        branches = supabase.table("branches").select("*").execute().data or []
        for branch in branches:
            st.text(f"📦 {branch['code']} - {branch.get('name', 'Unnamed')}")

        st.markdown("### ➕ Add New Branch")
        new_code = st.text_input("New Branch Code").strip()
        new_name = st.text_input("New Branch Name").strip()
        if st.button("Add Branch"):
            if new_code and new_name:
                exists = (
                    supabase.table("branches")
                    .select("code")
                    .eq("code", new_code.upper())
                    .execute()
                    .data
                )
                if exists:
                    st.error("Branch code already exists.")
                else:
                    try:
                        response = (
                            supabase.table("branches")
                            .insert(
                                {
                                    "code": new_code.upper(),
                                    "name": new_name,
                                    "riders": [],
                                }
                            )
                            .execute()
                        )
                        if response.data:
                            st.success("Branch added successfully.")
                            st.rerun()
                        else:
                            st.error("Failed to add branch: No data returned.")
                    except Exception as e:
                        st.error(f"Failed to add branch: {str(e)}")
            else:
                st.error("Please enter both branch code and name.")

        st.markdown("### ❌ Remove Branch")
        

        remove_code = st.text_input("Branch Code to Remove").strip()

        if st.button("Check Branch"):
            if not remove_code:
                st.error("Please enter a branch code to remove.")
            else:
                slips_resp = (
                    supabase.table("slips")
                    .select("*")
                    .eq("branch_code", remove_code.upper())
                    .execute()
                )
                slips = slips_resp.data or []

            if slips:
                st.warning(
                    f"Branch '{remove_code.upper()}' has {len(slips)} slip(s) linked. Deleting the branch will also delete these slips."
                )
                st.dataframe(slips)
                st.session_state["pending_delete_branch"] = remove_code.upper()
            else:
                branch_resp = (
                    supabase.table("branches")
                    .delete()
                    .eq("code", remove_code.upper())
                    .execute()
                )
                if branch_resp.error:
                    st.error(f"Error removing branch: {branch_resp.error['message']}")
                else:
                    st.success(f"Branch '{remove_code.upper()}' deleted successfully.")
                    st.session_state.pop("pending_delete_branch", None)
                    st.rerun()

    # Show confirm button only if there's a pending delete branch
    if "pending_delete_branch" in st.session_state:
        branch_to_delete = st.session_state["pending_delete_branch"]
        if st.button(f"Confirm Delete Branch {branch_to_delete} and linked slips"):
            try:
                supabase.table("slips").delete().eq(
                    "branch_code", branch_to_delete
                ).execute()
                supabase.table("branches").delete().eq(
                    "code", branch_to_delete
                ).execute()
                st.success(
                    f"Branch '{branch_to_delete}' and linked slips deleted successfully."
                )
            except Exception as e:
                st.error(f"Error during deletion: {str(e)}")
            finally:
                st.session_state.pop("pending_delete_branch", None)
                st.rerun()

    # --------- Rider Management ---------
    with tab2:
        st.subheader("Rider Assignment")
        code = st.text_input("Branch Code to Manage Riders").strip()
        if code:
            result = (
                supabase.table("branches")
                .select("*")
                .eq("code", code.upper())
                .single()
                .execute()
            )
            branch = result.data
            if not branch:
                st.error("Branch not found.")
            else:
                riders = branch.get("riders", [])

                st.markdown("### 🧾 Current Riders")
                if riders:
                    for rider in riders:
                        col1, col2 = st.columns([3, 1])
                        with col1:
                            st.write(rider)
                        with col2:
                            if st.button(f"Remove {rider}", key=f"rm_{rider}"):
                                updated = [r for r in riders if r != rider]
                                supabase.table("branches").update(
                                    {"riders": updated}
                                ).eq("code", code.upper()).execute()
                                st.success(f"Removed rider: {rider}")
                                st.rerun()
                else:
                    st.info("No riders assigned yet.")

                new_rider = st.text_input("Add New Rider").strip()
                if st.button("Add Rider"):
                    if new_rider:
                        if new_rider in riders:
                            st.warning("Rider already exists.")
                        else:
                            updated = riders + [new_rider]
                            supabase.table("branches").update({"riders": updated}).eq(
                                "code", code.upper()
                            ).execute()
                            st.success("Rider added.")
                            st.rerun()
                    else:
                        st.error("Please enter a rider name.")

    # --------- Change Request Submission ---------
    with tab3:
        st.subheader("Change Requests")
        desc = st.text_area("Request Description")
        if st.button("Submit Request"):
            if desc.strip():
                req = {
                    "timestamp": datetime.datetime.now().isoformat(),
                    "status": "Pending",
                    "description": desc.strip(),
                }
                supabase.table("requests").insert(req).execute()
                st.success("Request submitted.")
            else:
                st.error("Please enter a description.")

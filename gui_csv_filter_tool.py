import streamlit as st
import pandas as pd
import io
import hashlib

st.title("Cohort Creation with Sarvam")

# --- Authentication using st.secrets ---
USER_CREDENTIALS = st.secrets["USER_CREDENTIALS"]

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

with st.sidebar:
    st.header("Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    login_button = st.button("Login")

if login_button:
    if username in USER_CREDENTIALS and USER_CREDENTIALS[username] == password:
        st.session_state["authenticated"] = True
        st.success(f"Welcome, {username}!")
    else:
        st.error("Invalid username or password")

if not st.session_state.get("authenticated", False):
    st.stop()

# Upload Files
master_file = st.file_uploader("Upload Master CSV/XLSX (required)", type=["csv", "xlsx"])
interaction_file = st.file_uploader("Upload Interactions CSV (required)", type="csv")
add_file = st.file_uploader("Upload Add CSV/XLSX (optional)", type=["csv", "xlsx"])
stop_file = st.file_uploader("Upload Stop CSV/XLSX (optional)", type=["csv", "xlsx"])

# Option for keeping not connected
not_connected_to_keep = st.checkbox("Keep not connected users?", value=True)

if master_file and interaction_file:
    # Load Master
    if master_file.name.endswith(".csv"):
        master_df = pd.read_csv(master_file)
    else:
        master_df = pd.read_excel(master_file)

    # Load Interactions
    interactions_df = pd.read_csv(interaction_file)

    # Choose identifier column from master
    user_identifier_col_master = st.selectbox("Select the unique identifier column from master", master_df.columns)

    # Choose identifier column from interactions
    user_identifier_col_interactions = st.selectbox("Select the unique identifier column from interactions", interactions_df.columns)

    # Choose disposition column from interactions
    disposition_col = st.selectbox("Select the disposition column from interactions", interactions_df.columns)

    # Select disposition values to remove
    if disposition_col:
        dispositions = interactions_df[disposition_col].dropna().unique().tolist()
        removed_dispositions = st.multiselect("Select dispositions to remove", options=dispositions)

    # Trigger filtering
    if st.button("Generate Output"):
        if not_connected_to_keep:
            # Use master as base
            final_df = master_df.copy()

            # Step 1: Add entries
            if add_file:
                if add_file.name.endswith(".csv"):
                    add_df = pd.read_csv(add_file)
                else:
                    add_df = pd.read_excel(add_file)
                final_df = pd.concat([final_df, add_df], ignore_index=True)
                final_df = final_df.drop_duplicates(subset=[user_identifier_col_master])

            # Step 2: Remove entries
            if stop_file:
                if stop_file.name.endswith(".csv"):
                    stop_df = pd.read_csv(stop_file)
                else:
                    stop_df = pd.read_excel(stop_file)
                stop_ids = stop_df[user_identifier_col_master].unique()
                final_df = final_df[~final_df[user_identifier_col_master].isin(stop_ids)]

            # Step 3: Remove based on disposition from interactions
            if removed_dispositions:
                ids_to_remove = interactions_df[interactions_df[disposition_col].isin(removed_dispositions)][user_identifier_col_interactions].unique()
                final_df = final_df[~final_df[user_identifier_col_master].isin(ids_to_remove)]

        else:
            # Use interaction IDs that are NOT in removed dispositions
            if removed_dispositions:
                valid_ids = interactions_df[~interactions_df[disposition_col].isin(removed_dispositions)][user_identifier_col_interactions].unique()
            else:
                valid_ids = interactions_df[user_identifier_col_interactions].unique()

            final_df = master_df[master_df[user_identifier_col_master].isin(valid_ids)].copy()

            # Step 1: Add entries
            if add_file:
                if add_file.name.endswith(".csv"):
                    add_df = pd.read_csv(add_file)
                else:
                    add_df = pd.read_excel(add_file)
                final_df = pd.concat([final_df, add_df], ignore_index=True)
                final_df = final_df.drop_duplicates(subset=[user_identifier_col_master])

            # Step 2: Remove entries
            if stop_file:
                if stop_file.name.endswith(".csv"):
                    stop_df = pd.read_csv(stop_file)
                else:
                    stop_df = pd.read_excel(stop_file)
                stop_ids = stop_df[user_identifier_col_master].unique()
                final_df = final_df[~final_df[user_identifier_col_master].isin(stop_ids)]

        # Output result
        st.success("Filtering complete! Download your output below.")
        csv_output = final_df.to_csv(index=False).encode('utf-8')
        st.download_button("Download Output CSV", data=csv_output, file_name="output.csv", mime="text/csv")
else:
    st.warning("Please upload both Master and Interactions files to continue.")

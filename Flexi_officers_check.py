import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import time

# Function to load and process the data
def process_data(sap_df, roster_df):
    sap_df['Start Date'] = pd.to_datetime(sap_df['Start Date'])
    roster_df['Deployment Date'] = pd.to_datetime(roster_df['Deployment Date'])
    sap_df = sap_df.sort_values('Start Date').drop_duplicates('Pers.no.', keep='last')
    three_months_ago = datetime.now() - timedelta(days=90)
    flexi_officers = sap_df[(sap_df['Start Date'] <= three_months_ago) & 
                            (sap_df['Employee Group'] == 'Casual Labour')]
    roster_staff = roster_df['Personnel no.'].unique()
    no_record_staff_ids = set(roster_staff) - set(sap_df['Pers.no.'])
    no_record_staff = roster_df[roster_df['Personnel no.'].isin(no_record_staff_ids)].drop_duplicates('Personnel no.')
    no_record_staff['Flag'] = 'No Record'
    no_record_staff = no_record_staff[['Personnel no.', 'Person First Name', 'Person Last Name', 'Flag']]
    no_record_staff['Last Deployed Date'] = 'N/A'
    no_record_staff['Name'] = no_record_staff['Person First Name'] + ' ' + no_record_staff['Person Last Name']
    no_record_staff = no_record_staff[['Personnel no.', 'Name', 'Last Deployed Date', 'Flag']]
    no_record_staff.columns = ['Staff ID', 'Name', 'Last Deployed Date', 'Status']
    flagged_staff = flexi_officers[flexi_officers['Pers.no.'].isin(roster_staff)]
    flagged_staff['Flag'] = 'Not Worked'
    flagged_staff = flagged_staff[['Pers.no.', 'Last name First name', 'Start Date', 'Flag']].copy()
    flagged_staff.columns = ['Staff ID', 'Name', 'Last Deployed Date', 'Status']
    result_df = pd.concat([flagged_staff, no_record_staff])
    return result_df

# Streamlit app layout
st.title('Flexi Officers Status Tracker')

# Initialize session state variables
if 'processing_complete' not in st.session_state:
    st.session_state.processing_complete = False
if 'result_df' not in st.session_state:
    st.session_state.result_df = None

# Sidebar content
with st.sidebar:
    if not st.session_state.processing_complete:
        st.header("Upload SAP Data (Master)")
        sap_file = st.file_uploader("Choose the SAP file", type=["csv", "xlsx"], key="sap_file")
        
        st.header("Upload Roster Data (Staff Coming for Work)")
        roster_file = st.file_uploader("Choose the Roster file", type=["csv", "xlsx"], key="roster_file")

        run_check = st.button("Run Check")
        
        if run_check and sap_file and roster_file:
            # Initialize the progress bar and status text
            progress = st.progress(0)
            status_text = st.empty()

            # Record start time
            start_time = time.time()

            # Step 1: Loading SAP data
            status_text.text("Loading SAP data...")
            if sap_file.name.endswith('.csv'):
                sap_df = pd.read_csv(sap_file)
            else:
                sap_df = pd.read_excel(sap_file)
            progress.progress(25)

            # Step 2: Loading Roster data
            status_text.text("Loading Roster data...")
            if roster_file.name.endswith('.csv'):
                roster_df = pd.read_csv(roster_file)
            else:
                roster_df = pd.read_excel(roster_file)
            progress.progress(50)

            # Step 3: Processing the data
            status_text.text("Processing data...")
            st.session_state.result_df = process_data(sap_df, roster_df)
            progress.progress(75)

            # Step 4: Displaying results
            status_text.text("Displaying results...")
            progress.progress(100)

            # Record end time
            end_time = time.time()
            processing_time = end_time - start_time

            # Mark the processing as complete
            st.session_state.processing_complete = True

            # Display processing time
            st.write(f"Processing completed in {processing_time:.2f} seconds.")

    else:
        st.success("Processing complete. Download the results below or reset to upload new files.")
        reset_button = st.button("Reset for New Uploads")
        if reset_button:
            # Clear session state to allow new file uploads
            st.session_state.processing_complete = False
            st.session_state.result_df = None
            st.session_state.sap_file = None  # Reset file uploader
            st.session_state.roster_file = None  # Reset file uploader

# Main content: Display results if processing is complete
if st.session_state.result_df is not None:
    st.write("## Flagged Flexi Officers")
    st.dataframe(st.session_state.result_df)

    # Option to download the flagged data
    csv = st.session_state.result_df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="Download flagged officers data as CSV",
        data=csv,
        file_name='flagged_officers_summary.csv',
        mime='text/csv',
        key="download_button_final"  # Ensure unique key
    )

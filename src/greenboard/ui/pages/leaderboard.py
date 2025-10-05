import streamlit as st
import pandas as pd

st.set_page_config(page_title="Leaderboard", page_icon="🏆")

st.markdown("# 🌱 WPI Greenboard")
st.markdown("2025-2026 Academic Year")

# Create sample data for testing (anonymized student name, carbon emissions, and major)
data = {
    "Anonymous Caterpillar": {"emissions": 120, "major": "Computer Science"},
    "Anonymous Dragonfly": {"emissions": 95, "major": "Mechanical Engineering"},
    "Anonymous Walrus": {"emissions": 150, "major": "Electrical Engineering"},
    "Anonymous Penguin": {"emissions": 80, "major": "Computer Science"},
    "Anonymous Dolphin": {"emissions": 110, "major": "Biomedical Engineering"},
    "Anonymous Eagle": {"emissions": 130, "major": "Chemical Engineering"},
    "Anonymous Fox": {"emissions": 70, "major": "Computer Science"},
    "Anonymous Bear": {"emissions": 160, "major": "Mechanical Engineering"},
    "Anonymous Lion": {"emissions": 140, "major": "Electrical Engineering"},
    "Anonymous Tiger": {"emissions": 100, "major": "Biomedical Engineering"},
    "Anonymous Shark": {"emissions": 85, "major": "Civil Engineering"},
    "Anonymous Butterfly": {"emissions": 125, "major": "Chemical Engineering"},
    "Anonymous Owl": {"emissions": 105, "major": "Civil Engineering"},
    "Anonymous Rabbit": {"emissions": 90, "major": "Computer Science"},
    "Anonymous Turtle": {"emissions": 175, "major": "Mechanical Engineering"}
}

# Convert the data into a pandas DataFrame
df = pd.DataFrame([
    {"Name": name, "Carbon Emissions (kg CO2)": info["emissions"], "Major": info["major"]}
    for name, info in data.items()
])

# Add controls for filtering, number of entries per page, pagination, and search
st.sidebar.header("Leaderboard Controls")

# Filter by major
majors = ["All"] + sorted(df["Major"].unique().tolist())
selected_major = st.sidebar.selectbox("Filter by Major", majors)

# View mode dropdown
view_options = ["By Student", "By Major"]
view_mode = st.sidebar.selectbox("View Mode", view_options, index=0)  # Default to "By Student"
group_by_major = (view_mode == "By Major")

# Number of entries dropdown
entries_options = [5, 10, 15, 20, 25]
num_entries = st.sidebar.selectbox("Entries per page", entries_options, index=1)  # Default to 10

# Apply filters
filtered_df = df.copy()

# Filter by major
if selected_major != "All":
    filtered_df = filtered_df[filtered_df["Major"] == selected_major]

# Sort the DataFrame by carbon emissions (descending order)
filtered_df = filtered_df.sort_values(by="Carbon Emissions (kg CO2)", ascending=False)

# Display the leaderboard
if group_by_major:
    st.subheader("Emissions by Major (Oct 2025)")
    
    # Calculate average and median emissions by major
    major_stats = filtered_df.groupby("Major")["Carbon Emissions (kg CO2)"].agg(['mean', 'median']).reset_index()
    major_stats.columns = ["Major", "Average Emissions (kg CO2)", "Median Emissions (kg CO2)"]
    
    # Round to 1 decimal place for better readability
    major_stats["Average Emissions (kg CO2)"] = major_stats["Average Emissions (kg CO2)"].round(1)
    major_stats["Median Emissions (kg CO2)"] = major_stats["Median Emissions (kg CO2)"].round(1)
    
    # Sort by average emissions (descending)
    major_stats = major_stats.sort_values(by="Average Emissions (kg CO2)", ascending=False)
    
    # Pagination for major stats
    total_majors = len(major_stats)
    total_pages = (total_majors - 1) // num_entries + 1
    
    # Get current page from session state or default to 1
    if 'major_page' not in st.session_state:
        st.session_state.major_page = 1
    
    page = st.session_state.major_page
    start_idx = (page - 1) * num_entries
    end_idx = start_idx + num_entries
    display_major_stats = major_stats.iloc[start_idx:end_idx].copy()
    
    # Show pagination info and table
    if total_pages > 1:
        st.write(f"Showing majors {start_idx + 1}-{min(end_idx, total_majors)} of {total_majors}")
    
    display_major_stats = display_major_stats.reset_index(drop=True)
    display_major_stats.index = display_major_stats.index + 1 + (0 if total_pages <= 1 else (page - 1) * num_entries)
    display_major_stats.index.name = "Rank"
    
    st.table(display_major_stats)
    
    # Page selector below the table
    if total_pages > 1:
        col1, col2, col3, col4, col5 = st.columns([1, 2, 3, 2, 1])
        
        with col2:
            if st.button("← Previous", disabled=(page <= 1), key="major_prev", use_container_width=True):
                st.session_state.major_page = page - 1
                st.rerun()
        
        with col3:
            new_page = st.selectbox("Page", range(1, total_pages + 1), index=page-1, key="major_page_selector", label_visibility="collapsed")
            if new_page != st.session_state.major_page:
                st.session_state.major_page = new_page
                st.rerun()
        
        with col4:
            if st.button("Next →", disabled=(page >= total_pages), key="major_next", use_container_width=True):
                st.session_state.major_page = page + 1
                st.rerun()
else:
    st.subheader("Highest Emissions by Student (Oct 2025)")
    
    # Pagination for student data
    total_students = len(filtered_df)
    total_pages = (total_students - 1) // num_entries + 1
    
    # Get current page from session state or default to 1
    if 'student_page' not in st.session_state:
        st.session_state.student_page = 1
    
    page = st.session_state.student_page
    start_idx = (page - 1) * num_entries
    end_idx = start_idx + num_entries
    display_df = filtered_df.drop(columns=["Major"]).iloc[start_idx:end_idx].copy()
    
    # Show pagination info and table
    if total_pages > 1:
        st.write(f"Showing students {start_idx + 1}-{min(end_idx, total_students)} of {total_students}")
    
    display_df = display_df.reset_index(drop=True)
    display_df.index = display_df.index + 1 + (0 if total_pages <= 1 else (page - 1) * num_entries)
    display_df.index.name = "Rank"
    
    st.table(display_df)
    
    # Page selector below the table
    if total_pages > 1:
        col1, col2, col3, col4, col5 = st.columns([1, 2, 3, 2, 1])
        
        with col2:
            if st.button("← Previous", disabled=(page <= 1), key="student_prev", use_container_width=True):
                st.session_state.student_page = page - 1
                st.rerun()
        
        with col3:
            new_page = st.selectbox("Page", range(1, total_pages + 1), index=page-1, key="student_page_selector", label_visibility="collapsed")
            if new_page != st.session_state.student_page:
                st.session_state.student_page = new_page
                st.rerun()
        
        with col4:
            if st.button("Next →", disabled=(page >= total_pages), key="student_next", use_container_width=True):
                st.session_state.student_page = page + 1
                st.rerun()

# Footer
st.markdown("---")
st.markdown("Developed by WPI Greenboard Team for CS 542 - Database Management Systems")
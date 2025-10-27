import streamlit as st
import pandas as pd

st.set_page_config(page_title="Details", page_icon="📦")

st.markdown("# Anonymous Shark")
st.markdown("### Civil Engineering Major")

# Create sample data for testing (each entry represents a package, including the date delivered, weight, carrier, and carbon emissions)
data = [
    {"Date": "2024-09-01", "Weight (lbs)": 5, "Carrier": "FedEx", "Carbon Emissions (kg CO2e)": 0.4936, "Transport Mode": "Air", "Source": "Addison, IL", "Desitination": "Worcester, MA", "Distance (miles)": 831, "Main Transit Emissions (kg CO2e)": 0.4936, "Last Mile Emissions (kg CO2e)": 0.0009, "Tree needed (1 year)": 0.02, "Equivalent miles driven": 1.2},
]

# Assign emissions constants based on transport mode, carrier, and weight
transit_emission_factors = {
    "Air": 2.0,    # kg CO2 per lb
    "Ground": 1.0, # kg CO2 per lb
    "Ship": 0.5    # kg CO2 per lb
}

weight_emission_factors = {
    (0, 2): 1.0,     # 0 < weight ≤ 2 lbs
    (2, 5): 1.5,     # 2 < weight ≤ 5 lbs
    (5, 10): 2.0,    # 5 < weight ≤ 10 lbs
    (10, float('inf')): 2.5  # weight > 10 lbs
}

# Convert the data into a pandas DataFrame
df = pd.DataFrame(data)

# Show a timeline view of each package, where each has a card with its details, including a formula showing how the carbon emissions were calculated
st.markdown("## Package Delivery Timeline")

# Convert dates to datetime for proper sorting
df['Date'] = pd.to_datetime(df['Date'])
df_sorted = df.sort_values('Date')

for index, row in df_sorted.iterrows():    
    # Card container with border styling
    with st.container(border=True):
        # Header with date and package number prominently displayed
        st.markdown(f"### 📦 Package {index + 1} - {row['Date'].strftime('%B %d, %Y')}")
        
        # Package details in a clean layout
        col_details1, col_details2 = st.columns(2)
        
        with col_details1:
            st.metric("Weight", f"{row['Weight (lbs)']} lbs")
            st.metric("Carrier", row['Carrier'])
        
        with col_details2:
            st.metric("Transport Mode", row['Transport Mode'])
            st.metric("Carbon Emissions", f"{row['Carbon Emissions (kg CO2e)']:.2f} kg CO2e")

        with st.expander("📍 View Route Details", expanded=False):
            st.markdown(f"**Source:** {row['Source']}")
            st.markdown(f"**Destination:** {row['Desitination']}")
            st.markdown(f"**Distance:** {row['Distance (miles)']} miles")

        with st.expander("🚛 Emission Breakdown", expanded=False):
            st.markdown(f"**Main Transit Emissions:** {row['Main Transit Emissions (kg CO2e)']:.4f} kg CO2e")
            st.markdown(f"**Last Mile Emissions:** {row['Last Mile Emissions (kg CO2e)']:.4f} kg CO2e")

        with st.expander("🌳 Environmental Impact", expanded=False):
            st.markdown(f"**Trees Needed (1 year):** {row['Tree needed (1 year)']:.2f}")
            st.markdown(f"**Equivalent Miles Driven:** {row['Equivalent miles driven']:.2f} miles")

    st.markdown("<br>", unsafe_allow_html=True)
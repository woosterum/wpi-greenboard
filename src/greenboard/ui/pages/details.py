import streamlit as st
import pandas as pd
import requests
import os

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")

st.set_page_config(page_title="Details", page_icon="📦")

st.markdown("# Anonymous Shark")
st.markdown("### Civil Engineering Major")

# Package data format:
# PackageRead(
#     package_id=r[0],
#     tracking_number=r[1],
#     carrier_name=r[2],
#     service_type=r[3],
#     date_shipped=r[4],
#     total_emissions_kg=r[5],
#     distance_traveled=r[6]
# )

try:
    data = pd.DataFrame(requests.get(f"{API_BASE_URL}/packages/?limit=100").json()) 
except requests.exceptions.RequestException:
    st.error("❌ Cannot connect to API")

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
df['date_shipped'] = pd.to_datetime(df['date_shipped'])
df_sorted = df.sort_values('date_shipped', ascending=False)

for index, row in df_sorted.iterrows():    
    # Skip entries with missing data
    if pd.isnull(row['total_emissions_kg']):
        continue

    # Card container with border styling
    with st.container(border=True):
        # Header with date and package number prominently displayed
        st.markdown(f"### 📦 Package {index + 1}")
        st.caption(f"Delivered on {row['date_shipped'].strftime('%B %d, %Y')}")
        
        # Package details in a clean layout
        col_details1, col_details2 = st.columns(2)
        
        with col_details1:
            # st.markdown(f"**Distance:** {row['distance_traveled']} km")
            st.metric("Distance", row['distance_traveled'])
            # st.metric("Weight", f"{row['Weight (lbs)']} lbs")
            st.metric("Carrier", row['carrier_name'])
        
        with col_details2:
            # st.write(row)
            st.metric("Transport Mode", row['service_type'])
            st.metric("Carbon Emissions", f"{row['total_emissions_kg']:.2f} kg CO2e")

        # with st.expander("📍 View Route Details", expanded=False):
            # st.markdown(f"**Source:** {row['Source']}")
            # st.markdown(f"**Destination:** {row['Desitination']}")
            # st.markdown(f"**Distance:** {row['distance_traveled']} km")

        # with st.expander("🚛 Emission Breakdown", expanded=False):
        #     st.markdown(f"**Main Transit Emissions:** {row['Main Transit Emissions (kg CO2e)']:.4f} kg CO2e")
        #     st.markdown(f"**Last Mile Emissions:** {row['Last Mile Emissions (kg CO2e)']:.4f} kg CO2e")

        # with st.expander("🌳 Environmental Impact", expanded=False):
        #     st.markdown(f"**Trees Needed (1 year):** {row['Tree needed (1 year)']:.2f}")
        #     st.markdown(f"**Equivalent Miles Driven:** {row['Equivalent miles driven']:.2f} miles")

    st.markdown("<br>", unsafe_allow_html=True)
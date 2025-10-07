import streamlit as st
import pandas as pd

st.set_page_config(page_title="Details", page_icon="📦")

st.markdown("# Details")
st.markdown("Anonymous Shark - Civil Engineering")

# Create sample data for testing (each entry represents a package, including the date delivered, weight, carrier, and carbon emissions)
data = [
    {"Date": "2024-09-01", "Weight (lbs)": 5, "Carrier": "FedEx", "Carbon Emissions (kg CO2)": 0, "Transport Mode": "Air"},
    {"Date": "2024-09-05", "Weight (lbs)": 3, "Carrier": "UPS", "Carbon Emissions (kg CO2)": 0, "Transport Mode": "Ground"},
    {"Date": "2024-09-10", "Weight (lbs)": 10, "Carrier": "USPS", "Carbon Emissions (kg CO2)": 0, "Transport Mode": "Ground"},
    {"Date": "2024-09-15", "Weight (lbs)": 4, "Carrier": "DHL", "Carbon Emissions (kg CO2)": 0, "Transport Mode": "Air"},
    {"Date": "2024-09-20", "Weight (lbs)": 7, "Carrier": "FedEx", "Carbon Emissions (kg CO2)": 0, "Transport Mode": "Air"},
    {"Date": "2024-09-25", "Weight (lbs)": 6, "Carrier": "UPS", "Carbon Emissions (kg CO2)": 0, "Transport Mode": "Ground"},
    {"Date": "2024-09-30", "Weight (lbs)": 2, "Carrier": "USPS", "Carbon Emissions (kg CO2)": 0, "Transport Mode": "Ground"},
    {"Date": "2024-10-05", "Weight (lbs)": 1, "Carrier": "DHL", "Carbon Emissions (kg CO2)": 0, "Transport Mode": "Ship"},
    {"Date": "2024-10-10", "Weight (lbs)": 8, "Carrier": "FedEx", "Carbon Emissions (kg CO2)": 0, "Transport Mode": "Air"},
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

for entry in data:
    transit_factor = transit_emission_factors.get(entry["Transport Mode"], 1.0)
    weight_factor = next((v for (k, v) in weight_emission_factors.items() if k[0] < entry["Weight (lbs)"] <= k[1]), 1.0)
    entry["Carbon Emissions (kg CO2)"] = entry["Weight (lbs)"] * transit_factor * weight_factor

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
            st.metric("Carbon Emissions", f"{row['Carbon Emissions (kg CO2)']:.2f} kg CO₂")
        
        # Calculation details in an expandable section
        with st.expander("📊 View Emission Calculation", expanded=False):
            # Get the actual values used in calculation
            transit_factor = transit_emission_factors.get(row['Transport Mode'], 1.0)
            weight_range = next((k for k in weight_emission_factors.keys() if k[0] < row["Weight (lbs)"] <= k[1]), (0, 2))
            weight_factor = weight_emission_factors.get(weight_range, 1.0)
            
            st.markdown("**Formula:**")
            st.latex(r"""
                \text{Carbon Emissions} = \text{Weight} \times \text{Transit Factor} \times \text{Weight Factor}
            """)
            
            st.markdown("**Calculation with actual values:**")
            st.latex(rf"""
                {row['Carbon Emissions (kg CO2)']:.2f} = {row['Weight (lbs)']} \times {transit_factor} \times {weight_factor}
            """)
            
            st.markdown("**Factor Details:**")
            st.markdown(f"• **Transit Factor:** {transit_factor} kg CO₂/lb (for {row['Transport Mode']} transport)")
            
            # Handle display of weight range, especially for the infinity case
            if weight_range[1] == float('inf'):
                weight_range_display = f"{weight_range[0]}+ lbs"
            else:
                weight_range_display = f"{weight_range[0]}-{weight_range[1]} lbs"
            st.markdown(f"• **Weight Factor:** {weight_factor} (for {weight_range_display} packages)")    # Add some spacing between cards
    st.markdown("<br>", unsafe_allow_html=True)
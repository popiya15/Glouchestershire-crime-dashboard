import streamlit as st
from streamlit_folium import st_folium
import folium
from folium.plugins import MarkerCluster
from data_loader import load_and_clean_data  # ✅ Use centralized function

st.set_page_config(page_title="Crime Map View", layout="wide")
st.title("Crime Map View")

# Load central data
df = load_and_clean_data()

# Drop rows without location only for this map
df = df.dropna(subset=["latitude", "longitude"])

# Sidebar filters
st.sidebar.header("Filters")
selected_year = st.sidebar.selectbox("Select Year:", sorted(df["year"].unique()))

# Month order fix
months_order = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December"
]
month_options = sorted(df["month_name"].unique(), key=lambda x: months_order.index(x))
selected_month = st.sidebar.selectbox("Select Month:", month_options)

# Filter by selected time
filtered_df = df[(df["year"] == selected_year) & (df["month_name"] == selected_month)]

st.success(f"{len(filtered_df)} records for {selected_month} {selected_year}")

if filtered_df.empty:
    st.warning("No records for selected filters.")
else:
    m = folium.Map(location=[filtered_df["latitude"].mean(), filtered_df["longitude"].mean()], zoom_start=12)
    marker_cluster = MarkerCluster().add_to(m)

    for _, row in filtered_df.iterrows():
        folium.Marker([row["latitude"], row["longitude"]]).add_to(marker_cluster)

    st.subheader(f"Crime Map: {selected_month} {selected_year}")
    st_folium(m, width=700)

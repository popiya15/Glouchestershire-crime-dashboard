import streamlit as st
from streamlit_folium import st_folium
import folium
from folium.plugins import MarkerCluster
from data_loader import load_and_clean_data

# Page config with new title
st.set_page_config(page_title="Crime Location Explorer", page_icon="📍", layout="wide")
st.title("📍 Crime Location Explorer")

# Load data
df = load_and_clean_data()
df = df.dropna(subset=["latitude", "longitude"])  # Drop rows with missing lat/lon

# Sidebar filters
st.sidebar.header("Filters")

# Year filter (no default needed)
available_years = sorted(df["year"].unique())
selected_year = st.sidebar.selectbox("Select Year:", available_years)

# Month filter (defaults to February if available)
months_order = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December"
]
month_options = sorted(df["month_name"].unique(), key=lambda x: months_order.index(x))

default_month = "February"
default_month_index = month_options.index(default_month) if default_month in month_options else 0
selected_month = st.sidebar.selectbox("Select Month:", month_options, index=default_month_index)

# Filter by selected year and month
filtered_df = df[(df["year"] == selected_year) & (df["month_name"] == selected_month)]

st.success(f"{len(filtered_df)} records for {selected_month} {selected_year}")

if filtered_df.empty:
    st.warning("No records for selected filters.")
else:
    # Create folium map
    m = folium.Map(
        location=[filtered_df["latitude"].mean(), filtered_df["longitude"].mean()],
        zoom_start=12
    )
    marker_cluster = MarkerCluster().add_to(m)

    for _, row in filtered_df.iterrows():
        folium.Marker(
            [row["latitude"], row["longitude"]],
            popup=row.get("crime type", "No crime type info")
        ).add_to(marker_cluster)

    st.subheader(f"Crime Map: {selected_month} {selected_year}")
    st_folium(m, width=700)

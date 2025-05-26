import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
from data_loader import load_and_clean_data

# Load the cleaned crime data
df = load_and_clean_data()
df['date'] = pd.to_datetime(df['month_parsed'])

@st.cache_data
def load_census_data():
    census_path = r"C:/Users/Mick/Desktop/Master degree UEA/SEM2/Advance analytics/ONS Census data/Summary census data.csv"
    df = pd.read_csv(census_path)
    df.columns = df.columns.str.strip()
    df['Date'] = pd.to_datetime(df['Date'], format="%d-%m-%y", dayfirst=True)
    df['Year'] = df['Date'].dt.year
    return df

census_df = load_census_data()

# Sidebar filter
crime_types = df["crime type"].dropna().unique()
selected_crime = st.sidebar.multiselect("Filter Crime Type:", sorted(crime_types), default=list(crime_types))

# Date range filter
st.markdown("### Select Date Range")
col_date1, col_date2 = st.columns(2)
with col_date1:
    start_date = st.date_input("Start Date", value=df['date'].min())
with col_date2:
    end_date = st.date_input("End Date", value=df['date'].max())

filtered_df = df[
    (df["crime type"].isin(selected_crime)) &
    (df["date"] >= pd.to_datetime(start_date)) &
    (df["date"] <= pd.to_datetime(end_date))
]

census_filtered = census_df[
    (census_df["Date"] >= pd.to_datetime(start_date)) &
    (census_df["Date"] <= pd.to_datetime(end_date))
]

if not census_filtered.empty:
    happiness_val = round(census_filtered["SW Hapiness"].mean(), 2)
    anxiety_val = round(census_filtered["SW Anxiety"].mean(), 2)
    uk_happiness_val = round(census_filtered["UK Hapiness"].mean(), 2)
    uk_anxiety_val = round(census_filtered["UK Anxiety"].mean(), 2)
else:
    happiness_val = 0.0
    anxiety_val = 0.0
    uk_happiness_val = 0.0
    uk_anxiety_val = 0.0

# Load filtered GeoJSON
def load_gloucestershire_geojson():
    geojson_path = r"C:/Users/Mick/Desktop/Master degree UEA/SEM2/Advance analytics/lad.json"
    with open(geojson_path) as f:
        uk_geojson = json.load(f)
    gloucestershire_districts = ["Cheltenham", "Cotswold", "Forest of Dean", "Gloucester", "Stroud", "Tewkesbury"]
    filtered_features = [
        feature for feature in uk_geojson['features']
        if feature['properties'].get('LAD13NM') in gloucestershire_districts
    ]
    return {"type": "FeatureCollection", "features": filtered_features}

district_crime_data = filtered_df['city'].value_counts().reset_index()
district_crime_data.columns = ['District', 'Crime Count']

min_crime = district_crime_data['Crime Count'].min()
max_crime = district_crime_data['Crime Count'].max()

geojson = load_gloucestershire_geojson()

# Choropleth map
fig_map = px.choropleth(
    district_crime_data,
    geojson=geojson,
    locations='District',
    featureidkey="properties.LAD13NM",
    color='Crime Count',
    color_continuous_scale='Blues',
    range_color=[min_crime, max_crime],
    title=f'Crime Distribution in Gloucestershire Districts ({start_date} to {end_date})'
)
fig_map.update_geos(fitbounds="locations", visible=True, projection_type="mercator", showcoastlines=False, showsubunits=False)
fig_map.update_layout(margin={"r":0,"t":40,"l":0,"b":0}, height=420, paper_bgcolor="rgba(0,0,0,0)", geo=dict(bgcolor="rgba(0,0,0,0)"))

# Donut chart
def create_donut_chart(value, label, color, compare_val=None):
    alt_color = color + '33'  # Transparent version of the same color for background ring

    annotations = [
        dict(text=label, x=0.5, y=0.65, font_size=16, showarrow=False, font_color="white"),
        dict(text=f"{value:.2f}", x=0.5, y=0.5, font_size=24, showarrow=False, font_color=color)
    ]

    if compare_val is not None:
        diff = round(value - compare_val, 2)
        if diff > 0:
            icon = "\u2191"
            icon_color = "#00cc66"
        elif diff < 0:
            icon = "\u2193"
            icon_color = "#ff3333"
        else:
            icon = "="
            icon_color = "#cccccc"

        annotations.append(
            dict(text=f"{icon} {abs(diff):.2f}", x=0.5, y=0.36, font_size=14, showarrow=False, font_color=icon_color)
        )

    fig = go.Figure(data=[go.Pie(
        values=[value, 10 - value],
        hole=0.7,
        marker_colors=[color, alt_color],
        textinfo='none',
        sort=False
    )])
    fig.update_layout(
        showlegend=False,
        margin=dict(t=0, b=0, l=0, r=0),
        annotations=annotations,
        width=220,
        height=220,
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)"
    )
    return fig

happiness_fig = create_donut_chart(happiness_val, "Happiness", "#00cc66", compare_val=uk_happiness_val)
anxiety_fig = create_donut_chart(anxiety_val, "Anxiety", "#ff3333", compare_val=uk_anxiety_val)

# Line chart: Crime over time
crime_timeline = (
    filtered_df.groupby(filtered_df['date'].dt.to_period('M'))
    .size()
    .reset_index(name='Crime Count')
)
crime_timeline['date'] = crime_timeline['date'].dt.to_timestamp()

fig_line = px.line(
    crime_timeline,
    x='date',
    y='Crime Count',
    title='Crime Over Time',
    markers=True
)
fig_line.update_layout(margin=dict(t=40, b=0), height=300, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")

# Layout: 3 columns
col1, col2, col3 = st.columns([1.5, 4.5, 2], gap='medium')

with col1:
    # Total Crime Card
    st.markdown(
        f"""
        <div style="background-color: #1e1e1e; padding: 20px; border-radius: 10px; text-align: center; color: white;">
            <div style="font-size: 18px; color: #cccccc;">Total Crime Cases</div>
            <div style="font-size: 36px; font-weight: bold; color: white;">{len(filtered_df):,}</div>
        </div>
        """,
        unsafe_allow_html=True
    )

    # Wellbeing Title
    st.markdown(
        """
        <div style="margin-top: 20px; text-align: center; font-size: 18px; color: #cccccc;">
            Wellbeing Indicators
        </div>
        """,
        unsafe_allow_html=True
    )

    # Donut charts (moved up)
    st.plotly_chart(happiness_fig, use_container_width=False)
    st.plotly_chart(anxiety_fig, use_container_width=False)

with col2:
    st.plotly_chart(fig_map, use_container_width=True)
    st.plotly_chart(fig_line, use_container_width=True)

with col3:
    table_df = district_crime_data[['District', 'Crime Count']].copy()
    st.dataframe(
        table_df,
        column_order=("District", "Crime Count"),
        hide_index=True,
        column_config={
            "District": st.column_config.TextColumn("City"),
            "Crime Count": st.column_config.ProgressColumn(
                "Crime Count",
                min_value=0,
                max_value=max(table_df["Crime Count"]),
                format="%d"
            )
        }
    )

    # Treemap: Crime type distribution
    crime_type_counts = (
        filtered_df["crime type"]
        .value_counts()
        .reset_index()
    )
    crime_type_counts.columns = ["Crime Type", "Count"]

    if not crime_type_counts.empty:
        min_count = crime_type_counts["Count"].min()
        max_count = crime_type_counts["Count"].max()
        crime_type_counts["ColorValue"] = 1 - (
        (crime_type_counts["Count"] - min_count) / (max_count - min_count)
    )
        crime_type_counts["Group"] = ""
        fig_treemap = px.treemap(
        crime_type_counts,
        path=["Group", "Crime Type"],
        values="Count",
        color="ColorValue",  # ✅ ใช้ column ที่เราคุมเอง
        color_continuous_scale = [
        "#bf360c",
        "#d84315",
        "#e64a19",
        "#f4511e",
        "#ff5722",
        "#ff7043",
        "#ff8a65",
        "#ffab91",
        "#ffccbc",
        "#fbe9e7"
        ],
        range_color=[0, 1]
        )
        fig_treemap.update_traces(
            root_color="rgba(0,0,0,0)",
            tiling=dict(pad=0),
            textinfo="label+value+percent entry",
            textfont=dict(color="white"),
            marker=dict(line=dict(width=0, color="rgba(0,0,0,0)"))
        )
        fig_treemap.update_layout(
            coloraxis_showscale=False,  
            margin=dict(t=0, b=0, l=0, r=0),
            height=500,  
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="white"),
            uniformtext=dict(minsize=10, mode='hide')
        )
        st.plotly_chart(fig_treemap, use_container_width=True)
    else:
        st.markdown("*No crime type data available for selected filters.*")

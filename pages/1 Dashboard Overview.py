import streamlit as st
st.set_page_config(layout="wide")

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
import os
from data_loader import load_and_clean_data

# Load crime data
df = load_and_clean_data()
df['date'] = pd.to_datetime(df['month_parsed'])

@st.cache_data
def load_census_data():
    census_path = "summary_census_data.csv"
    if not os.path.exists(census_path):
        st.error("Census data file not found. Please make sure 'summary_census_data.csv' is in the root directory.")
        return pd.DataFrame()
    df = pd.read_csv(census_path)
    df.columns = df.columns.str.strip()
    df['Date'] = pd.to_datetime(df['Date'], format="%d-%m-%y", dayfirst=True)
    df['Year'] = df['Date'].dt.year
    return df

census_df = load_census_data()

# Sidebar filter
crime_types = df["crime type"].dropna().unique()
selected_crime = st.sidebar.multiselect("Filter Crime Type:", sorted(crime_types), default=list(crime_types))

# Date filter
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
    happiness_val = anxiety_val = uk_happiness_val = uk_anxiety_val = 0.0

# Load GeoJSON
@st.cache_data
def load_geojson():
    geo_path = "lad.json"
    if not os.path.exists(geo_path):
        st.error("GeoJSON file not found. Please place 'lad.json' in the root directory.")
        return {"type": "FeatureCollection", "features": []}
    with open(geo_path) as f:
        geojson = json.load(f)
    keep_districts = ["Cheltenham", "Cotswold", "Forest of Dean", "Gloucester", "Stroud", "Tewkesbury"]
    filtered = [f for f in geojson['features'] if f['properties'].get('LAD13NM') in keep_districts]
    return {"type": "FeatureCollection", "features": filtered}

geojson = load_geojson()

district_crime_data = filtered_df['city'].value_counts().reset_index()
district_crime_data.columns = ['District', 'Crime Count']
min_crime, max_crime = district_crime_data['Crime Count'].min(), district_crime_data['Crime Count'].max()

# Choropleth map
fig_map = px.choropleth(
    district_crime_data,
    geojson=geojson,
    locations='District',
    featureidkey="properties.LAD13NM",
    color='Crime Count',
    color_continuous_scale='Blues',
    range_color=[min_crime, max_crime]
)
fig_map.update_geos(fitbounds="locations", visible=False)
fig_map.update_layout(margin=dict(t=40, b=0, l=0, r=0), height=420, paper_bgcolor="rgba(0,0,0,0)", geo=dict(bgcolor="rgba(0,0,0,0)"))

# Donut chart
def create_donut_chart(value, label, color, compare_val=None):
    alt_color = color + '33'
    annotations = [
        dict(text=label, x=0.5, y=0.65, font_size=16, showarrow=False, font_color="white"),
        dict(text=f"{value:.2f}", x=0.5, y=0.5, font_size=24, showarrow=False, font_color=color)
    ]
    if compare_val is not None:
        diff = round(value - compare_val, 2)
        icon = "↑" if diff > 0 else "↓" if diff < 0 else "="
        icon_color = "#00cc66" if diff > 0 else "#ff3333" if diff < 0 else "#cccccc"
        annotations.append(dict(text=f"{icon} {abs(diff):.2f}", x=0.5, y=0.36, font_size=14, showarrow=False, font_color=icon_color))
    fig = go.Figure(data=[go.Pie(values=[value, 10 - value], hole=0.7, marker_colors=[color, alt_color], textinfo='none', sort=False)])
    fig.update_layout(showlegend=False, margin=dict(t=0, b=0, l=0, r=0), annotations=annotations, width=220, height=220, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
    return fig

# Timeline (line chart)
timeline = filtered_df.groupby(filtered_df['date'].dt.to_period('M')).size().reset_index(name='Crime Count')
timeline['date'] = timeline['date'].dt.to_timestamp()

min_y = timeline['Crime Count'].min()
max_y = timeline['Crime Count'].max()
padding = (max_y - min_y) * 0.1

fig_line = px.line(
    timeline, 
    x='date', 
    y='Crime Count', 
    title='Crime Over Time', 
    markers=True
)

fig_line.update_xaxes(range=[timeline['date'].min(), timeline['date'].max()], rangebreaks=[])
fig_line.update_yaxes(range=[min_y - padding, max_y + padding])

fig_line.update_layout(
    margin=dict(t=40, b=0),
    height=300,
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)"
)
fig_line.update_yaxes(range=[3000, max_y + padding])


# Treemap
crime_type_counts = filtered_df["crime type"].value_counts().reset_index()
crime_type_counts.columns = ["Crime Type", "Count"]

if not crime_type_counts.empty:
    min_count = crime_type_counts["Count"].min()
    max_count = crime_type_counts["Count"].max()
    crime_type_counts["ColorValue"] = 1 - ((crime_type_counts["Count"] - min_count) / (max_count - min_count))
    crime_type_counts["Group"] = "Crime Types"
    fig_treemap = px.treemap(
        crime_type_counts,
        path=["Group", "Crime Type"],
        values="Count",
        color="ColorValue",
        color_continuous_scale=[
            "#263238",  # dark blue-grey
    "#455A64",
    "#607D8B",
    "#90A4AE",
    "#CFD8DC"
        ],
        range_color=[0, 1]
    )
    fig_treemap.update_traces(
        root_color="rgba(30,30,30,1)",
        tiling=dict(pad=0),
        textinfo="label+value+percent entry",
        textfont=dict(color="white"),
        marker=dict(line=dict(width=0, color="rgba(0,0,0,0)"))
    )
    fig_treemap.update_layout(
        coloraxis_showscale=False,
        margin=dict(t=0, b=0, l=0, r=0),
        height=250,
        paper_bgcolor="rgba(30,30,30,1)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="white"),
        uniformtext=dict(minsize=10, mode='hide')
    )
else:
    fig_treemap = None

# Layout 3 columns
col1, col2, col3 = st.columns([1.5, 4.5, 2], gap='medium')

with col1:
    st.markdown(f"""
        <div style="background-color: #1e1e1e; padding: 20px; border-radius: 10px; text-align: center; color: white;">
            <div style="font-size: 18px; color: #cccccc;">Total Crime Cases</div>
            <div style="font-size: 36px; font-weight: bold; color: white;">{len(filtered_df):,}</div>
        </div>
    """, unsafe_allow_html=True)
    st.markdown("<div style='margin-top: 20px; text-align: center; font-size: 18px; color: #cccccc;'>Wellbeing Indicators</div>", unsafe_allow_html=True)
    st.plotly_chart(create_donut_chart(happiness_val, "Happiness", "#00cc66", uk_happiness_val), use_container_width=False)
    st.plotly_chart(create_donut_chart(anxiety_val, "Anxiety", "#ff3333", uk_anxiety_val), use_container_width=False)

with col2:
    st.plotly_chart(fig_map, use_container_width=True)
    if fig_treemap:
        st.plotly_chart(fig_treemap, use_container_width=True)
    else:
        st.markdown("*No crime type data available for selected filters.*")

with col3:
    # Crime by City Table
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

    # About Box
    with st.expander("About", expanded=True):
         st.markdown("""
    <style>
    .about-box {
        font-size: 13px;
        line-height: 1.4;
        max-width: 340px;
        max-height: 250px;
        overflow-y: auto;
        padding-right: 10px;
    }
    .about-box ul {
        padding-left: 18px;
        margin: 0;
    }
    .about-box li {
        margin-bottom: 6px;
    }
    .about-box a {
        color: #80caff;
        text-decoration: none;
    }
    .about-box a:hover {
        text-decoration: underline;
    }
    .highlight {
        color: #f1c40f;
        font-weight: 600;
    }
    .light-desc {
        font-weight: 300;
        font-size: 12px;
        display: inline-block;
        margin-top: 2px;
    }
    </style>

    <div class="about-box">
        <ul>
            <li><span>Data Sources</span><br>
                <span class="light-desc">
                    <a href='https://data.police.uk/data/' target='_blank'>UK Police Crime Data</a>, 
                    <a href='https://www.ons.gov.uk/peoplepopulationandcommunity/wellbeing/datasets/quarterlypersonalwellbeingestimatesnonseasonallyadjusted' target='_blank'>ONS Wellbeing Estimates</a>
                </span>
            </li>
            <li><span class="highlight">Wellbeing Metrics</span><br>
                <span class="light-desc">
                    Arrow indicators compare South West values to the UK average
                </span>
            </li>
            <li><span class="highlight">Crime Statistics</span><br>
                <span class="light-desc">
                    Monthly aggregated data by district with geographic and categorical breakdowns
                </span>
            </li>
        </ul>
    </div>
    """, unsafe_allow_html=True)


st.plotly_chart(fig_line, use_container_width=True)